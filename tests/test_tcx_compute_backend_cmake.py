from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ASTRA_ROOT = Path(__file__).resolve().parents[1]
ANALYTICAL_SOURCE = ASTRA_ROOT / "build" / "astra_analytical"
FAKE_SOURCE = ASTRA_ROOT / "tests" / "fake_compute_backend"
CHAKRA_PROTO_DIR = (
    ASTRA_ROOT / "extern" / "graph_frontend" / "chakra" / "schema" / "protobuf"
)
GENERATED_PROTO = (
    CHAKRA_PROTO_DIR / "et_def.pb.cc",
    CHAKRA_PROTO_DIR / "et_def.pb.h",
    CHAKRA_PROTO_DIR / "et_def_pb2.py",
)


def run(
    *args: str,
    check: bool = False,
    env=None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        check=check,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def package_search_controls() -> list[str]:
    return [
        "-DCMAKE_FIND_USE_PACKAGE_REGISTRY=FALSE",
        "-DCMAKE_FIND_USE_SYSTEM_PACKAGE_REGISTRY=FALSE",
        "-DCMAKE_FIND_PACKAGE_NO_PACKAGE_REGISTRY=TRUE",
        "-DCMAKE_FIND_PACKAGE_NO_SYSTEM_PACKAGE_REGISTRY=TRUE",
    ]


class TcxComputeBackendCMakeTest(unittest.TestCase):
    def test_off_configures_without_external_package(self):
        with tempfile.TemporaryDirectory(prefix="astra-off-") as tmp:
            result = run(
                "cmake",
                "-S", str(ANALYTICAL_SOURCE),
                "-B", str(Path(tmp) / "build"),
                "-DBUILDTARGET=congestion_aware",
                "-DCMAKE_DISABLE_FIND_PACKAGE_TcxComputeBackend=TRUE",
                *package_search_controls(),
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            cache = (Path(tmp) / "build" / "CMakeCache.txt").read_text()
            self.assertIn("ASTRA_ENABLE_TCX_COMPUTE_BACKEND:BOOL=OFF", cache)

    def test_on_rejects_missing_package(self):
        with tempfile.TemporaryDirectory(prefix="astra-missing-") as tmp:
            result = run(
                "cmake",
                "-S", str(ANALYTICAL_SOURCE),
                "-B", str(Path(tmp) / "build"),
                "-DBUILDTARGET=congestion_aware",
                "-DASTRA_ENABLE_TCX_COMPUTE_BACKEND=ON",
                "-DCMAKE_PREFIX_PATH=" + str(Path(tmp) / "absent"),
                "-DTcxComputeBackend_DIR=" + str(Path(tmp) / "absent"),
                *package_search_controls(),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("TcxComputeBackend", result.stdout)

    def test_on_accepts_installed_fake_target(self):
        source_before = {
            path: path.read_bytes() if path.exists() else None
            for path in GENERATED_PROTO
        }
        with tempfile.TemporaryDirectory(prefix="astra-fake-") as tmp:
            root = Path(tmp)
            fake_build = root / "fake-build"
            prefix = root / "prefix"
            astra_build = root / "astra-build"
            run(
                "cmake", "-S", str(FAKE_SOURCE), "-B", str(fake_build),
                "-DCMAKE_INSTALL_PREFIX=" + str(prefix),
                check=True,
            )
            run("cmake", "--build", str(fake_build), "--target", "install", check=True)
            result = run(
                "cmake",
                "-S", str(ANALYTICAL_SOURCE),
                "-B", str(astra_build),
                "-DBUILDTARGET=congestion_aware",
                "-DASTRA_ENABLE_TCX_COMPUTE_BACKEND=ON",
                "-DTcxComputeBackend_DIR="
                + str(prefix / "lib" / "cmake" / "TcxComputeBackend"),
                *package_search_controls(),
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            run(
                "cmake", "--build", str(astra_build),
                "--target", "AstraSim_Analytical_Congestion_Aware",
                "-j", "2",
                check=True,
            )
            compile_flags = "\n".join(
                path.read_text(encoding="utf-8")
                for path in astra_build.rglob("flags.make")
            )
            self.assertIn("ASTRA_ENABLE_TCX_COMPUTE_BACKEND=1", compile_flags)
            link_commands = "\n".join(
                path.read_text(encoding="utf-8")
                for path in astra_build.rglob("link.txt")
            )
            self.assertIn("libtcx_fake_compute_backend.a", link_commands)
        self.assertEqual(
            {
                path: path.read_bytes() if path.exists() else None
                for path in GENERATED_PROTO
            },
            source_before,
        )

    def test_config_mode_uses_modern_protobuf_generation(self):
        cmake_text = (ASTRA_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
        self.assertNotIn("protobuf_generate_cpp", cmake_text)
        self.assertIn("protobuf_generate(", cmake_text)
        with tempfile.TemporaryDirectory(prefix="astra-protobuf-config-") as tmp:
            root = Path(tmp)
            config_dir = root / "protobuf-config"
            config_dir.mkdir()
            (config_dir / "protobuf-config.cmake").write_text(
                "find_package(Protobuf MODULE REQUIRED)\n",
                encoding="utf-8",
            )
            astra_build = root / "astra-build"
            environment = os.environ.copy()
            environment["PROTOBUF_FROM_SOURCE"] = "True"
            result = run(
                "cmake",
                "-S", str(ANALYTICAL_SOURCE),
                "-B", str(astra_build),
                "-DBUILDTARGET=congestion_aware",
                "-Dprotobuf_DIR=" + str(config_dir),
                "-DASTRA_ENABLE_TCX_COMPUTE_BACKEND=OFF",
                env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            run(
                "cmake", "--build", str(astra_build),
                "--target", "AstraSim",
                "-j", "2",
                check=True,
                env=environment,
            )


if __name__ == "__main__":
    unittest.main()
