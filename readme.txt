Crimson Desert Key Rebind Tool
==============================

What this does
--------------
This tool reads the original (vanilla) inputmap.xml and inputmap_common.xml files from Crimson Desert, lets you pick new movement and menu keys through a simple GUI, and writes the modified files into the Movement_keys_rebind mod folder.

How to use
----------
1. Make sure the vanilla source files are in the "vanilla_sources_files" folder next to this executable:
      vanilla_sources_files/inputmap.xml
      vanilla_sources_files/inputmap_common.xml

2. Run the executable:
      Windows : double-click CrimsonKeyRebind.exe
      Linux   : double-click CrimsonKeyRebind or run it from a terminal

3. Fill in the keys you want to use (for example Up = w, Left = a, etc.).
      Menu navigation keys (left/right) and menu slot keys are allowed to overlap by design.
      Only movement keys (up/down/left/right) must be unique.
      Entered keys must be in the usable key list shown by the app.

4. Click "Generate files".

5. The tool will overwrite the files inside:
      Movement_keys_rebind/files/0012/ui/inputmap.xml
      Movement_keys_rebind/files/0012/ui/inputmap_common.xml

6. Import the "Movement_keys_rebind" folder into your mod manager and enable it.

Notes
-----
- w a s d become rebindable
- The vanilla source files are never modified.
- Clicking "Generate files" again will overwrite the output files in Movement_keys_rebind.
- Movement_keys_rebind is the folder you import into the mod manager.
