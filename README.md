# beatsaber-version-manager
You have modded beatsaber and there is a pending update on steam and you dont want to risk all your installed mods because they maight not be working?

Prevent update:
modifies the appmanifest from beatsabers so that steam thinks the newest version is installed. Works with ManifestID from https://steamdb.info/depot/620981/manifests/

Revert update:
the update started accidently? enables steam console with https://github.com/fifty-six/zig.SteamManifestPatcher (auto download and execution) and run command to download old version (the version the mods are installed for) and replaces the files automaticly
