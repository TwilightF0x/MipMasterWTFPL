import ctypes
import os
import subprocess
import threading
from typing import List

from PIL import Image


class ExportService:
    def __init__(self, assembler_lib_path: str, compressor_exe: str, nv_compressor_exe: str):
        self.assembler_lib_path = os.path.abspath(assembler_lib_path)
        self.compressor_exe = compressor_exe
        self.nv_compressor_exe = nv_compressor_exe
        self._assembler_lib = None
        self._dll_dir_handles = []

    def export_mips(
        self,
        folder_path: str,
        output_filename: str,
        extension: str,
        strict_size: bool,
        min_mip: int,
        max_mip: int,
        original_mips: list,
        mips: list,
        mip_options_getter,
        apply_effects_fn,
        make_array: bool,
        bc_format: str,
        cleanup: bool,
    ) -> List[str]:
        processed_mips = []

        for i, _ in enumerate(original_mips):
            if i < min_mip or i > max_mip:
                continue

            if mips[i] is None:
                options = mip_options_getter(i)
                mips[i] = apply_effects_fn(original_mips[i], options)

            export_path = (
                f"{folder_path}/mip_{i}{extension}"
                if not strict_size
                else f"{folder_path}/{output_filename}{extension}"
            )
            mips[i].save(export_path)
            processed_mips.append(export_path)

        if make_array and not strict_size and bc_format not in ("R8G8B8A8_UNORM", "R32G32B32A32_FLOAT"):
            self._assemble_and_compress(folder_path, output_filename, processed_mips, bc_format)
        elif bc_format in ("R8G8B8A8_UNORM", "R32G32B32A32_FLOAT"):
            self._assemble_raw_dds(folder_path, output_filename, processed_mips, bc_format)

        if cleanup and not strict_size:
            self._cleanup_intermediate(folder_path, processed_mips)

        return processed_mips

    def _get_assembler_lib(self):
        if self._assembler_lib is not None:
            return self._assembler_lib

        if not os.path.exists(self.assembler_lib_path):
            raise FileNotFoundError(f"MipAssembler DLL not found: {self.assembler_lib_path}")

        dll_dir = os.path.dirname(self.assembler_lib_path)
        fallback_release_dir = os.path.join(dll_dir, "MipCAssembler", "MipAssembler", "x64", "Release")
        search_dirs = [dll_dir]
        if os.path.isdir(fallback_release_dir):
            search_dirs.append(fallback_release_dir)

        for search_dir in search_dirs:
            if hasattr(os, "add_dll_directory"):
                self._dll_dir_handles.append(os.add_dll_directory(search_dir))

        try:
            assembler_lib = ctypes.cdll.LoadLibrary(self.assembler_lib_path)
        except OSError as exc:
            raise RuntimeError(f"Failed to load MipAssembler DLL: {exc}") from exc

        string_array_type = ctypes.POINTER(ctypes.c_wchar_p)
        assembler_lib.AssembleMipsToDDS.argtypes = [
            string_array_type,
            ctypes.c_int,
            ctypes.c_wchar_p,
        ]
        assembler_lib.AssembleMipsToDDS.restype = ctypes.c_bool
        self._assembler_lib = assembler_lib
        return self._assembler_lib

    def _assemble_mips(self, mip_files: List[str], output_path: str):
        if not mip_files:
            raise RuntimeError("No mip files provided for DDS assembly.")

        normalized_mips = []
        for mip_path in mip_files:
            normalized = os.path.normpath(os.path.abspath(mip_path))
            if not os.path.exists(normalized):
                raise FileNotFoundError(f"Mip source file not found: {normalized}")
            normalized_mips.append(normalized)

        normalized_output = os.path.normpath(os.path.abspath(output_path))
        prepared_mips = []
        for idx, mip_path in enumerate(normalized_mips):
            prepared_path = os.path.normpath(f"{normalized_output}.prepared_{idx}.tga")
            with Image.open(mip_path) as src:
                src.save(prepared_path, format="TGA")
            prepared_mips.append(prepared_path)

        thread_result = {"success": False, "error": ""}

        def _dll_call_worker():
            try:
                arr_type = ctypes.c_wchar_p * len(prepared_mips)
                c_input_array = arr_type(*prepared_mips)
                thread_result["success"] = bool(
                    self._get_assembler_lib().AssembleMipsToDDS(
                        c_input_array,
                        len(prepared_mips),
                        normalized_output,
                    )
                )
            except Exception as worker_exc:
                thread_result["error"] = str(worker_exc)

        worker = threading.Thread(target=_dll_call_worker, daemon=True)
        worker.start()
        worker.join()

        for prepared_path in prepared_mips:
            if os.path.exists(prepared_path):
                os.remove(prepared_path)

        if thread_result["error"]:
            raise RuntimeError(f"MipAssembler.dll call failed in worker: {thread_result['error']}")
        if not thread_result["success"]:
            raise RuntimeError("MipAssembler.dll failed to assemble DDS texture.")

    def _assemble_and_compress(self, folder_path: str, output_filename: str, processed_mips: List[str], bc_format: str):
        interim_dds_path = os.path.normpath(f"{folder_path}/Interim_result_output.dds")
        self._assemble_mips(processed_mips, interim_dds_path)

        nv_compress_cmd_call = [
            os.path.normpath(self.nv_compressor_exe),
            "-" + str(bc_format).lower(),
            "-silent",
            "-max-mip-count",
            f"{len(processed_mips)}",
            interim_dds_path,
            os.path.normpath(f"{folder_path}/{output_filename}.dds"),
        ]
        subprocess.run(nv_compress_cmd_call, check=True, capture_output=True, text=True)

    def _assemble_raw_dds(self, folder_path: str, output_filename: str, processed_mips: List[str], _bc_format: str):
        self._assemble_mips(
            processed_mips,
            os.path.normpath(f"{folder_path}/{output_filename}.dds"),
        )

    def _cleanup_intermediate(self, folder_path: str, processed_mips: List[str]):
        for path in processed_mips:
            if os.path.exists(path):
                os.remove(path)

        interim = os.path.normpath(f"{folder_path}/Interim_result_output.dds")
        if os.path.exists(interim):
            os.remove(interim)
