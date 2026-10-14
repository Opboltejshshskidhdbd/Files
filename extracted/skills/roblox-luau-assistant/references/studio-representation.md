# Roblox Studio Representation Reference

Use for project trees, installation steps, source maps, and READMEs.

Canonical identity: `Instance.Name + Instance.ClassName + Parent/Service`.
Export identity: `filename + extension + source`.

Studio tree: `ObjectName (ClassName)`. Export package: filenames may use `.server.lua`, `.client.lua`, `.luau`, etc. Keep the views explicitly separated.

Required mapping: Source File → Parent/Service → Instance.Name → Instance.ClassName.

Representation defects include wrong class/parent/name, missing class where ambiguous, installation instructions that tell users to copy filenames instead of create Instances, pseudo-file UI/remotes, or README/source-map/audit disagreement.

Text representation is static documentation evidence only; do not claim Studio runtime placement unless runtime artifacts exist.
