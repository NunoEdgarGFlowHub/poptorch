#!/usr/bin/env python3
# Copyright (c) 2020 Graphcore Ltd. All rights reserved.

import torch
import torch.nn as nn
import poptorch

import pytest

# Tensors

# Creation ops (we don't support many of these)
# torch.numel, torch.tensor, torch.sparse_coo_tensor, torch.as_tensor, torch.as_strided, torch.from_numpy, torch.zeros,
# torch.zeros_like, torch.ones, torch.ones_like, torch.arange, torch.range, torch.linspace, torch.logspace, torch.eye,
# torch.empty, torch.empty_like, torch.empty_strided, torch.full, torch.full_like, torch.quantize_per_tensor, torch.quantize_per_channel,

# Indexing, Slicing, Joining, Mutating Ops
# torch.cat, torch.chunk, torch.gather, torch.index_select, torch.masked_select, torch.narrow, torch.nonzero, torch.reshape, torch.split,
# torch.squeeze, torch.stack, torch.t, torch.take, torch.transpose, torch.unbind, torch.unsqueeze, torch.where, torch._C.Generator,
# torch._C.Generator.device,


def test_zeros_and_ones():
    class Model(torch.nn.Module):
        def forward(self):
            x = torch.zeros(3, 5, 1)
            y = torch.ones(3, 5, 1)

            # A stupid test to stop popart from prunning this.
            return x * y, y + x

    model = Model()

    # Run on CPU.
    nativeOut = model()

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model()

    assert torch.equal(nativeOut[0], poptorch_out[0])
    assert torch.equal(nativeOut[1], poptorch_out[1])


def test_cat():
    class Model(torch.nn.Module):
        def forward(self, x):
            return torch.cat((x, x, x), 0)

    model = Model()
    x = torch.randn(2, 3)

    # Run on CPU.
    nativeOut = model(x)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x)

    assert nativeOut.size() == poptorch_out.size()
    assert torch.equal(nativeOut, poptorch_out)


def test_chunk():
    class Model(torch.nn.Module):
        def forward(self, x):
            return torch.chunk(x, 5)

    model = Model()
    x = torch.randn(20, 10)

    # Run on CPU.
    nativeOut = model(x)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x)

    for native, pop in zip(nativeOut, poptorch_out):
        assert torch.equal(native, pop)


def test_reshape():
    class Model(torch.nn.Module):
        def forward(self, x):
            return torch.reshape(x, (1, 1, 2, 2))

    model = Model()
    x = torch.arange(4.)

    # Run on CPU.
    nativeOut = model(x)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x)

    assert nativeOut.size() == poptorch_out.size()
    assert torch.equal(nativeOut, poptorch_out)


def test_split():
    class Model(torch.nn.Module):
        def forward(self, x):
            return torch.split(x, 5)

    model = Model()
    x = torch.randn(20, 10)

    # Run on CPU.
    nativeOut = model(x)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x)

    for native, pop in zip(nativeOut, poptorch_out):
        assert torch.equal(native, pop)


def test_squeeze():
    class Model(torch.nn.Module):
        def forward(self, x):
            return torch.squeeze(x)

    model = Model()
    x = torch.randn(1, 1, 20, 1, 10, 1)

    # Run on CPU.
    nativeOut = model(x)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x)

    assert nativeOut.size() == poptorch_out.size()
    assert torch.equal(nativeOut, poptorch_out)


def test_t():
    class Model(torch.nn.Module):
        def forward(self, x):
            return torch.t(x)

    model = Model()
    x = torch.randn(20, 10)

    # Run on CPU.
    nativeOut = model(x)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x)

    assert nativeOut.size() == poptorch_out.size()
    assert torch.equal(nativeOut, poptorch_out)


def test_transpose():
    class Model(torch.nn.Module):
        def forward(self, x):
            return torch.transpose(x, 3, 0)

    model = Model()
    x = torch.randn(3, 2, 5, 10)

    # Run on CPU.
    nativeOut = model(x)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x)

    assert nativeOut.size() == poptorch_out.size()
    assert torch.equal(nativeOut, poptorch_out)


def test_unsqueeze():
    class Model(torch.nn.Module):
        def forward(self, x):
            return torch.unsqueeze(x, 1)

    model = Model()
    x = torch.randn(3, 2, 5, 10)

    # Run on CPU.
    nativeOut = model(x)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x)

    assert nativeOut.size() == poptorch_out.size()
    assert torch.equal(nativeOut, poptorch_out)


def test_expand():
    class Model(torch.nn.Module):
        def forward(self, x):
            return x.expand(3, 4)

    model = Model()
    x = torch.randn(3, 1)

    # Run on CPU.
    nativeOut = model(x)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x)

    assert nativeOut.size() == poptorch_out.size()
    assert torch.equal(nativeOut, poptorch_out)


def test_expand_as():
    class Model(torch.nn.Module):
        def forward(self, x, y):
            return x.expand_as(y)

    model = Model()
    x = torch.randn(3, 1)
    y = torch.randn(3, 4)

    # Run on CPU.
    nativeOut = model(x, y)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x, y)

    assert nativeOut.size() == poptorch_out.size()
    assert torch.equal(nativeOut, poptorch_out)


def test_flatten():
    class Model(torch.nn.Module):
        def forward(self, x):
            return torch.flatten(x)

    model = Model()
    x = torch.randn(3, 1)

    # Run on CPU.
    nativeOut = model(x)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x)

    assert nativeOut.size() == poptorch_out.size()
    assert torch.equal(nativeOut, poptorch_out)


def test_view():
    class Model(torch.nn.Module):
        def forward(self, x):
            return x.view((15, 2, 5))

    model = Model()
    x = torch.randn(30, 5)

    # Run on CPU.
    nativeOut = model(x)

    # Run on IPU.
    poptorch_model = poptorch.inferenceModel(model)
    poptorch_out = poptorch_model(x)

    assert nativeOut.size() == poptorch_out.size()
    assert torch.equal(nativeOut, poptorch_out)


t = torch.tensor([[[1, 2], [3, 4]], [[5, 6], [7, 8]]])