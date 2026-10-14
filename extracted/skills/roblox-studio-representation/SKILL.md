---
name: roblox-studio-representation
description: Roblox Studio-native representation for project trees, installation steps, source maps, and READMEs only.
---

# ROBLOX DEV MASTER — Studio Representation v1.1

Load this skill only when the task concerns project trees, Studio installation instructions, source maps, or README representation.

Studio identity = `Instance.Name + Instance.ClassName + Parent/Service`. Export identity = `filename + extension + source`. Never treat them as interchangeable.

Studio trees use `ObjectName (ClassName)`: `StealAFishServer (Script)`, `StealAFishClient (LocalScript)`, `Config (ModuleScript)`, `StartSteal (RemoteEvent)`, `MainFrame (Frame)`. Do not make users infer Script type from `.server.lua` or `.client.lua`.

Installation must say which Roblox Instance to create, where, and what class it is. When source packages are discussed, label the filesystem/export view separately and preserve explicit Source File → Parent/Service → Instance.Name → Instance.ClassName mapping.

README/source-map/audit representation must agree. A wrong class, parent, name, or mapping is a representation/source-architecture defect. Runtime Studio placement is unverified unless actual runtime artifacts exist.
