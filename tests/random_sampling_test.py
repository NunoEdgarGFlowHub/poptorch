#!/usr/bin/env python3
# Copyright (c) 2020 Graphcore Ltd. All rights reserved.
import torch
import pytest
import poptorch


# Random Number Generation Harness
# Checks that the IPU generated data with roughly the same summary statistics as the CPU version
def rng_harness(rng_op, stat_funs):
    class Model(torch.nn.Module):
        def __init__(self):
            super(Model, self).__init__()
            self.rng_op = rng_op

        def forward(self):
            return self.rng_op()

    model = Model()

    # Run on CPU
    native_out = model()

    # Run on IPU
    opts = poptorch.Options().randomSeed(8)
    pop_model = poptorch.inferenceModel(model, opts)
    pop_out = pop_model()

    assert native_out.size() == pop_out.size()

    # PRNG depends on HW implementation so we just check
    # that the distribution statistics are consistent
    print("Checking summary statistics for generated random numbers:")
    for ss in stat_funs:
        print("  {} = {}".format(ss.__name__, ss(pop_out)))
        torch.testing.assert_allclose(ss(native_out),
                                      ss(pop_out),
                                      atol=1e-2,
                                      rtol=0.1)


# torch.rand
# Filter the following expected warnings
@pytest.mark.filterwarnings("ignore:Trace had nondeterministic nodes")
@pytest.mark.filterwarnings(
    "ignore:Output nr 1. of the traced function does not match")
@pytest.mark.skipif(not poptorch.ipuHardwareIsAvailable(),
                    reason="Hardware IPU needed")
def test_rand():
    def rng_op():
        torch.manual_seed(42)
        return torch.rand(3, 5, 100)

    stat_funs = [torch.min, torch.max, torch.mean, torch.var]

    rng_harness(rng_op, stat_funs)


# torch.distributions.uniform.Uniform
# Filter the following expected warnings
@pytest.mark.filterwarnings("ignore:Trace had nondeterministic nodes")
@pytest.mark.filterwarnings(
    "ignore:Output nr 1. of the traced function does not match")
@pytest.mark.filterwarnings(
    "ignore:torch.Tensor results are registered as constants in the trace")
@pytest.mark.skipif(not poptorch.ipuHardwareIsAvailable(),
                    reason="Hardware IPU needed")
def test_distributions_uniform():
    def rng_op():
        torch.manual_seed(42)
        ud = torch.distributions.uniform.Uniform(0.0, 10.0)
        return ud.sample((10, 10, 1000))

    stat_funs = [torch.min, torch.max, torch.mean, torch.var]

    rng_harness(rng_op, stat_funs)


# torch.uniform_
# Filter the following expected warnings
@pytest.mark.filterwarnings("ignore:Trace had nondeterministic nodes")
@pytest.mark.filterwarnings(
    "ignore:Output nr 1. of the traced function does not match")
@pytest.mark.skipif(not poptorch.ipuHardwareIsAvailable(),
                    reason="Hardware IPU needed")
def test_uniform_():
    def rng_op():
        torch.manual_seed(42)
        return torch.empty((3, 4, 1000)).uniform_()

    stat_funs = [torch.min, torch.max, torch.mean, torch.var]

    rng_harness(rng_op, stat_funs)


# torch.normal
# Filter the following expected warnings
@pytest.mark.filterwarnings("ignore:Trace had nondeterministic nodes")
@pytest.mark.filterwarnings(
    "ignore:Output nr 1. of the traced function does not match")
@pytest.mark.skipif(not poptorch.ipuHardwareIsAvailable(),
                    reason="Hardware IPU needed")
def test_normal():
    def rng_op():
        torch.manual_seed(42)
        return torch.normal(mean=0.0, std=1.0, size=(6, 10, 1000))

    stat_funs = [torch.mean, torch.var]

    rng_harness(rng_op, stat_funs)


# torch.normal_
# Filter the following expected warnings
@pytest.mark.filterwarnings("ignore:Trace had nondeterministic nodes")
@pytest.mark.filterwarnings(
    "ignore:Output nr 1. of the traced function does not match")
@pytest.mark.skipif(not poptorch.ipuHardwareIsAvailable(),
                    reason="Hardware IPU needed")
def test_normal_():
    def rng_op():
        torch.manual_seed(42)
        return torch.empty(3, 5, 1000).normal_(mean=1.0, std=2.0)

    stat_funs = [torch.mean, torch.var]

    rng_harness(rng_op, stat_funs)


# torch.distributions.Normal
# The sample method uses torch.normal(Tensor mean, Tensor std)
# Filter the following expected warnings
@pytest.mark.filterwarnings("ignore:Trace had nondeterministic nodes")
@pytest.mark.filterwarnings(
    "ignore:Output nr 1. of the traced function does not match")
@pytest.mark.filterwarnings(
    "ignore:torch.Tensor results are registered as constants in the trace")
@pytest.mark.skipif(not poptorch.ipuHardwareIsAvailable(),
                    reason="Hardware IPU needed")
def test_distributions_normal():
    def rng_op():
        torch.manual_seed(42)
        h = torch.tensor([234.0, 100.0])
        nd = torch.distributions.Normal(loc=h, scale=torch.sqrt(h))
        return nd.sample((10000, 5))

    # Generates (10000, 5, 2) tensor
    mean = lambda x: torch.mean(x, dim=[0, 1])
    mean.__name__ = "torch.mean(x, dim=[0, 1])"

    std = lambda x: torch.std(x, dim=[0, 1])
    std.__name__ = "torch.std(x, dim=[0, 1])"

    stat_funs = [mean, std]

    rng_harness(rng_op, stat_funs)


# torch.randn
# Filter the following expected warnings
@pytest.mark.filterwarnings("ignore:Trace had nondeterministic nodes")
@pytest.mark.filterwarnings(
    "ignore:Output nr 1. of the traced function does not match")
@pytest.mark.skipif(not poptorch.ipuHardwareIsAvailable(),
                    reason="Hardware IPU needed")
def test_randn():
    def rng_op():
        torch.manual_seed(42)
        return torch.randn(3, 5, 10000)

    stat_funs = [torch.mean, torch.var]

    rng_harness(rng_op, stat_funs)


# torch.normal(Tensor mean, float std)
# Filter the following expected warnings
@pytest.mark.filterwarnings("ignore:Trace had nondeterministic nodes")
@pytest.mark.filterwarnings(
    "ignore:Output nr 1. of the traced function does not match")
@pytest.mark.filterwarnings(
    "ignore:torch.Tensor results are registered as constants in the trace")
@pytest.mark.skipif(not poptorch.ipuHardwareIsAvailable(),
                    reason="Hardware IPU needed")
def test_normal_tensor_mean():
    def rng_op():
        torch.manual_seed(42)
        mean = torch.full(size=(10000, 2), fill_value=4.0)
        std = 3.0
        return torch.normal(mean=mean, std=std)

    stat_funs = [torch.mean, torch.std]

    rng_harness(rng_op, stat_funs)


# torch.normal(float mean, Tensor std)
# Filter the following expected warnings
@pytest.mark.filterwarnings("ignore:Trace had nondeterministic nodes")
@pytest.mark.filterwarnings(
    "ignore:Output nr 1. of the traced function does not match")
@pytest.mark.filterwarnings(
    "ignore:torch.Tensor results are registered as constants in the trace")
@pytest.mark.skipif(not poptorch.ipuHardwareIsAvailable(),
                    reason="Hardware IPU needed")
def test_normal_tensor_std():
    def rng_op():
        torch.manual_seed(42)
        mean = 3.0
        std = torch.full(size=(10000, 2), fill_value=9.0)
        return torch.normal(mean=mean, std=std)

    stat_funs = [torch.mean, torch.std]

    rng_harness(rng_op, stat_funs)


# Filter the following expected warnings
@pytest.mark.filterwarnings("ignore:Trace had nondeterministic nodes")
@pytest.mark.filterwarnings(
    "ignore:Output nr 1. of the traced function does not match")
@pytest.mark.parametrize("t", [torch.float, torch.half])
@pytest.mark.skipif(not poptorch.ipuHardwareIsAvailable(),
                    reason="Hardware IPU needed")
def test_normal_half(t):
    class Model(torch.nn.Module):
        def forward(self, x):
            torch.manual_seed(42)
            x.normal_(mean=20.0, std=8.0)
            return x

    model = Model()
    input_data = torch.ones(3, 5, 1000, dtype=t)

    # Run on IPU and check that the result has the correct dtype
    opts = poptorch.Options().randomSeed(8)
    pop_model = poptorch.inferenceModel(model, opts)
    pop_out = pop_model(input_data)
    assert pop_out.dtype == t

    if t is not torch.half:
        # Run on CPU
        native_out = model(input_data)
        assert native_out.size() == pop_out.size()

    # Test summary stats - promoting half to float to workaround
    # torch limitations with half
    torch.testing.assert_allclose(20.0,
                                  torch.mean(pop_out.float()),
                                  atol=1e-2,
                                  rtol=0.1)

    torch.testing.assert_allclose(8.0,
                                  torch.std(pop_out.float()),
                                  atol=1e-2,
                                  rtol=0.1)


# Filter the following expected warnings
@pytest.mark.filterwarnings("ignore:Trace had nondeterministic nodes")
@pytest.mark.filterwarnings(
    "ignore:Output nr 1. of the traced function does not match")
@pytest.mark.parametrize("t", [torch.float, torch.half])
@pytest.mark.skipif(not poptorch.ipuHardwareIsAvailable(),
                    reason="Hardware IPU needed")
def test_uniform_half(t):
    class Model(torch.nn.Module):
        def forward(self, x):
            torch.manual_seed(42)
            x.uniform_(-1, 1)
            return x

    model = Model()
    input_data = torch.ones(3, 5, 1000, dtype=t)

    # Run on IPU and check that the result has the correct dtype
    opts = poptorch.Options().randomSeed(8)
    pop_model = poptorch.inferenceModel(model, opts)
    pop_out = pop_model(input_data)
    assert pop_out.dtype == t

    if t is not torch.half:
        # Run on CPU
        native_out = model(input_data)
        assert native_out.size() == pop_out.size()

    # Test summary stats - promoting half to float to workaround
    # torch limitations with half
    torch.testing.assert_allclose(-1.0,
                                  torch.min(pop_out.float()),
                                  atol=1e-2,
                                  rtol=0.1)

    torch.testing.assert_allclose(1.0,
                                  torch.max(pop_out.float()),
                                  atol=1e-2,
                                  rtol=0.1)


# Filter the following expected warnings
@pytest.mark.filterwarnings(
    "ignore:Output nr 1. of the traced function does not match")
@pytest.mark.skipif(not poptorch.ipuHardwareIsAvailable(),
                    reason="Hardware IPU needed")
def test_random_seed_repeatability():
    class Model(torch.nn.Module):
        def forward(self, x):
            return x.normal_()

    # Run the model once with a random seed
    model = Model()
    opts = poptorch.Options().randomSeed(42)
    first_model = poptorch.inferenceModel(model, opts)
    first_run = first_model(torch.empty((2, 2)))

    # Second run with the same seed should produce identical results
    second_model = poptorch.inferenceModel(model, opts)
    second_run = second_model(torch.empty((2, 2)))
    assert torch.equal(first_run, second_run)
