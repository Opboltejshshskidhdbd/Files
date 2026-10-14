# Luau Syntax Knowledge Expansion v1.0

## Authority
Official Luau documentation is the language authority. Generic Lua material is only a compatibility/background source and must not be treated as Luau syntax truth when it conflicts with Luau documentation.

Official anchors checked during this upgrade:
- `https://luau.org/`
- `https://github.com/luau-lang/site`
- `https://github.com/luau-lang/luau`

## Classification
Every syntax fact is classified as one of:
- `VALID_LUAU`
- `INVALID_LUAU`
- `VALID_LUA_BUT_NOT_LUAU`
- `VALID_LUAU_BUT_CONTEXT_UNSUPPORTED`
- `ROBLOX_SPECIFIC`
- `TYPE_SYSTEM_ONLY`
- `UNCERTAIN`

## Coverage
Track and retrieve knowledge for:
- baseline Lua 5.1 syntax
- Luau string/number literal extensions
- `continue`
- compound assignment
- if-expressions
- interpolation
- type annotations
- unions/intersections/singletons
- generics and generic type packs
- function types and overloads
- type refinement
- casts and `typeof`
- variadic arguments and type packs
- metatables
- attributes and Luau syntax keywords/features
- compatibility boundaries with later Lua versions
- malformed block/control-flow structure
- malformed callbacks and generated source composition

## Important official syntax evidence
The official Luau syntax documentation states that Luau uses Lua 5.1 as a baseline and adds Luau-specific syntax. It also documents `continue`, including its placement restrictions, and Luau-specific string/number literal behavior. Therefore generic Lua 5.x examples must not automatically be copied into Roblox Luau code.

## Learning rule
A syntax error is not a lesson by itself. A lesson requires reproduction, root-cause analysis, actual repair, revalidation, and a useful generalized prevention/detection rule.
