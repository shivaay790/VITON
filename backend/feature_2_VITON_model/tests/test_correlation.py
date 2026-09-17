"""The PyTorch correlation layer must match DM-VTON's CUDA kernel exactly.

The reference below transcribes the kernel's index arithmetic line for line,
kernel_Correlation_rearrange then kernel_Correlation_updateOutput, rather than
restating what it is meant to compute. No GPU, dataset or weights needed.

    python -m pytest feature_2_VITON_model/tests      (from backend/)
    python feature_2_VITON_model/tests/test_correlation.py
"""

import math
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DM-VTON"))
from models.common.correlation import FunctionCorrelation, correlation_torch  # noqa: E402


def kernel_reference(first, second, stride):
    n_batch, channels, height, width = first.shape
    padded_h, padded_w = height + 6 * stride, width + 6 * stride
    rbot0 = torch.zeros(n_batch, padded_h, padded_w, channels, dtype=first.dtype)
    rbot1 = torch.zeros(n_batch, padded_h, padded_w, channels, dtype=first.dtype)
    for n in range(n_batch):
        for index in range(height * width):
            y = index // width + 3 * stride
            x = index % width + 3 * stride
            rbot0[n, y, x] = first[n, :, index // width, index % width]
            rbot1[n, y, x] = second[n, :, index // width, index % width]

    out_h, out_w = math.ceil(height / stride), math.ceil(width / stride)
    top = torch.zeros(n_batch, 49, out_h, out_w, dtype=first.dtype)
    for item in range(n_batch):
        for block_y in range(out_h):
            for block_x in range(out_w):
                x1 = (block_x + 3) * stride
                y1 = (block_y + 3) * stride
                for channel in range(49):
                    s2o = (channel % 7 - 3) * stride
                    s2p = (channel // 7 - 3) * stride
                    total = (rbot0[item, y1, x1] * rbot1[item, y1 + s2p, x1 + s2o]).sum()
                    top[item, channel, block_y, block_x] = total / channels
    return top


def test_matches_cuda_kernel_arithmetic():
    torch.manual_seed(0)
    # Odd sizes and strides above 1 exercise the ceil and the padding edges.
    for n, c, h, w, s in [(1, 4, 7, 9, 1), (2, 3, 8, 5, 1), (1, 5, 9, 11, 2), (2, 2, 6, 7, 2), (1, 3, 10, 10, 3)]:
        a = torch.randn(n, c, h, w, dtype=torch.float64)
        b = torch.randn(n, c, h, w, dtype=torch.float64)
        expected = kernel_reference(a, b, s)
        got = correlation_torch(a, b, s)
        assert got.shape == expected.shape
        assert torch.allclose(got, expected, atol=1e-12), (n, c, h, w, s)


def test_entry_point_runs_on_cpu_with_gradients():
    a = torch.randn(1, 4, 12, 10, requires_grad=True)
    b = torch.randn(1, 4, 12, 10, requires_grad=True)
    FunctionCorrelation(tenFirst=a, tenSecond=b, intStride=1).sum().backward()
    assert a.grad is not None and b.grad is not None


if __name__ == "__main__":
    test_matches_cuda_kernel_arithmetic()
    test_entry_point_runs_on_cpu_with_gradients()
    print("correlation tests passed")
