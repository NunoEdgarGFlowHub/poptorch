// Copyright (c) 2020 Graphcore Ltd. All rights reserved.
#ifndef INCLUDE_POPTORCH_OP_BUILDER_HPP
#define INCLUDE_POPTORCH_OP_BUILDER_HPP
#include <torch/csrc/jit/ir/ir.h>

#include <string>
#include <tuple>
#include <utility>
#include <vector>

#include "poptorch/ImplicitCasting.hpp"

namespace poptorch {
torch::jit::Node *createAndInsertNode(
    torch::jit::Graph *graph, torch::jit::NodeKind kind,
    torch::jit::ArrayRef<torch::jit::Value *> inputs = {},
    ImplicitCast implicit_cast = ImplicitCast::None,
    ImplicitCastOutput implicit_cast_output = ImplicitCastOutput::None,
    size_t num_outputs = 1);

// Create a poptorch::tensor_constant node from the given tensors, setting the
// output type accordingly
torch::jit::Node *tensorToConstant(torch::jit::Graph *graph,
                                   const at::Tensor &t);

// Manually added.
torch::jit::Node *createReshape(torch::jit::Graph *graph, torch::jit::Value *A,
                                const std::vector<int64_t> &new_shape);

torch::jit::Node *createConstantInt(torch::jit::Graph *graph,
                                    const std::vector<int64_t> &data,
                                    const std::vector<int64_t> &new_shape);

torch::jit::Node *createConstantFloat(torch::jit::Graph *graph,
                                      const std::vector<double> &data,
                                      const std::vector<int64_t> &new_shape);

torch::jit::Node *createConstantFloat16(torch::jit::Graph *graph,
                                        const std::vector<double> &data,
                                        const std::vector<int64_t> &new_shape);

torch::jit::Node *
createCustomOperation(torch::jit::Graph *graph,
                      const std::vector<torch::jit::Value *> &inputs,
                      const std::string &name, const std::string &domain,
                      std::int64_t domainVersion, std::int64_t numOutputs);

torch::jit::Node *createCast(torch::jit::Graph *graph, torch::jit::Value *A,
                             c10::ScalarType scalar);

torch::jit::Node *createConstantPad(torch::jit::Graph *graph,
                                    torch::jit::Value *A,
                                    const std::vector<int64_t> &pad_shape,
                                    float constant);

torch::jit::Node *createReflectionPad(torch::jit::Graph *graph,
                                      torch::jit::Value *A,
                                      const std::vector<int64_t> &pad_shape);

torch::jit::Node *createEdgePad(torch::jit::Graph *graph, torch::jit::Value *A,
                                const std::vector<int64_t> &pad_shape);

torch::jit::Node *createAddNotInPlace(torch::jit::Graph *graph,
                                      torch::jit::Value *A,
                                      torch::jit::Value *B);

template <typename... Ints,
          std::enable_if_t<std::is_integral<typename std::tuple_element<
                               0, std::tuple<Ints...>>::type>::value,
                           int> = 0>
torch::jit::Value *wrapInConstant1D(torch::jit::Graph *graph, Ints... values) {
  std::vector<int64_t> data{std::forward<Ints>(values)...};
  return createConstantInt(graph, data,
                           {static_cast<std::int64_t>(data.size())})
      ->output();
}

template <typename... Floats,
          std::enable_if_t<std::is_floating_point<typename std::tuple_element<
                               0, std::tuple<Floats...>>::type>::value,
                           int> = 0>
torch::jit::Value *wrapInConstant1D(torch::jit::Graph *graph,
                                    Floats... values) {
  std::vector<double> data{std::forward<Floats>(values)...};
  return createConstantFloat(graph, data,
                             {static_cast<std::int64_t>(data.size())})
      ->output();
}

// Ops which will return the correct ScalarType

torch::jit::Node *createCastTypedOutput(torch::jit::Graph *graph,
                                        torch::jit::Value *A,
                                        c10::ScalarType scalar);

torch::jit::Node *
createConcatTypedOutput(torch::jit::Graph *graph,
                        const std::vector<torch::jit::Value *> &args,
                        int64_t axis);

torch::jit::Node *
createFlattenTypedOutput(torch::jit::Graph *graph,
                         const std::vector<torch::jit::Value *> &args,
                         int64_t axis);

torch::jit::Node *createSplitTypedOutput(
    torch::jit::Graph *graph, const std::vector<torch::jit::Value *> &args,
    unsigned int num_outputs, int64_t axis, const std::vector<int64_t> &split);

torch::jit::Node *
createTransposeTypedOutput(torch::jit::Graph *graph,
                           const std::vector<torch::jit::Value *> &args,
                           const std::vector<int64_t> &perm);

// Used to add to the output the same type as in input to a unary create
// function
torch::jit::Node *createUnarySameTypedOutput(
    torch::jit::Node *(*create_fn)(torch::jit::Graph *,
                                   const std::vector<torch::jit::Value *> &),
    torch::jit::Graph *graph, const std::vector<torch::jit::Value *> &args);

template <typename CreateFn, typename... Args>
torch::jit::Node *
createWithSameTypedOutput(CreateFn &&create_fn, torch::jit::Graph *graph,
                          const std::vector<torch::jit::Value *> &args,
                          Args &&... op_args) {
  torch::jit::Node *new_node =
      create_fn(graph, args, std::forward<Args>(op_args)...);
  new_node->output()->setType(args[0]->type());
  return new_node;
}

// Default to int in the helper.
template <typename T> struct CreateConstant {
  torch::jit::Node *operator()(torch::jit::Graph *graph,
                               const std::vector<int64_t> &data,
                               const std::vector<int64_t> &new_shape) {
    return createConstantInt(graph, data, new_shape);
  }
};

template <> struct CreateConstant<float> {
  torch::jit::Node *operator()(torch::jit::Graph *graph,
                               const std::vector<double> &data,
                               const std::vector<int64_t> &new_shape) {
    return createConstantFloat(graph, data, new_shape);
  }
};

template <typename T> struct CreateCast {};

template <> struct CreateCast<float> {
  torch::jit::Node *operator()(torch::jit::Graph *graph,
                               torch::jit::Value *value) {
    return createCast(graph, value, c10::kFloat);
  }
};

template <> struct CreateCast<std::int32_t> {
  torch::jit::Node *operator()(torch::jit::Graph *graph,
                               torch::jit::Value *value) {
    return createCast(graph, value, c10::kInt);
  }
};

template <> struct CreateCast<std::int64_t> {
  torch::jit::Node *operator()(torch::jit::Graph *graph,
                               torch::jit::Value *value) {
    return createCast(graph, value, c10::kLong);
  }
};

template <typename T>
torch::jit::Node *castToType(torch::jit::Graph *graph,
                             torch::jit::Value *value) {
  return CreateCast<T>{}(graph, value);
}

torch::jit::Node *createRandomNormal(torch::jit::Graph *graph,
                                     const std::vector<int64_t> &shape,
                                     float mean, float scale,
                                     at::ScalarType dataType);

torch::jit::Node *createRandomUniform(torch::jit::Graph *graph,
                                      const std::vector<int64_t> &shape,
                                      float high, float low,
                                      at::ScalarType dataType);

torch::jit::Node *createSetAvailableMemory(torch::jit::Graph *graph,
                                           torch::jit::Value *value,
                                           float proportion);

// Autogenerated.
#include "CompilerOps.inc.hpp"

} // namespace poptorch

#endif // INCLUDE_POPTORCH_OP_BUILDER_HPP
