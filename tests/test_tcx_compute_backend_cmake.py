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


def run(*args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


class TcxComputeBackendCMakeTest(unittest.TestCase):
    def test_off_configures_without_external_package(self):
        with tempfile.TemporaryDirectory(prefix="astra-off-") as tmp:
            result = run(
                "cmake",
                "-S", str(ANALYTICAL_SOURCE),
                "-B", str(Path(tmp) / "build"),
                "-DBUILDTARGET=congestion_aware",
                "-DASTRA_ENABLE_TCX_COMPUTE_BACKEND=OFF",
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
                "-DCMAKE_PREFIX_PATH=" + str(prefix),
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            run(
                "cmake", "--build", str(astra_build),
                "--target", "AstraSim_Analytical_Congestion_Aware",
                "-j", "2",
                check=True,
            )
        self.assertEqual(
            {
                path: path.read_bytes() if path.exists() else None
                for path in GENERATED_PROTO
            },
            source_before,
        )


if __name__ == "__main__":
    unittest.main()
