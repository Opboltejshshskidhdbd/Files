# Roblox Studio Representation Reference

This reference is the detailed contract for the `roblox-studio-representation` skill.

## Canonical model

`Studio Object = Instance.Name + Instance.ClassName + Parent/Service`

`Export File = filename + extension + source`

Studio representation and filesystem representation are separate views of the same implementation.

## Required mapping fields

For every important source object, preserve:
- Studio Instance.Name
- Studio ClassName
- Parent/service
- Execution context when applicable
- Purpose
- Export filename when one exists

## Canonical Studio tree

```text
Workspace
├── ...
ReplicatedStorage
├── ...
ServerScriptService
├── ...
StarterPlayer
└── StarterPlayerScripts
    └── ...
```

Important nodes use `Name (ClassName)`.

## Export mapping

```text
Studio Object: FooServer
Class: Script
Parent: ServerScriptService
Export File: FooServer.server.lua
```

The export filename is metadata for the source package, not the Instance.Name.

## Defect classification

Treat these as representation/source-architecture defects:
- README says LocalScript while architecture requires Script.
- Source map assigns a client file to ServerScriptService as a Script.
- Studio tree omits ClassName for an important created script when class is ambiguous.
- Installation tells a Studio user to copy a filename rather than create the correct Instance.
- UI/remote Instances are represented as pseudo-files in Studio-facing output.
- README, audit, source map, and generated architecture disagree about object name/class/parent.

## Verification boundary

A representation audit is a static/source/documentation verification unless Roblox Studio is actually executed. Do not claim runtime placement verification from a text tree alone.
