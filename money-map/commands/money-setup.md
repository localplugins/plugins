---
description: Set up money-map for your data — create the categories & rules file and confirm how your export's columns map.
argument-hint: "[path-to-a-sample-export.csv]"
---

# Money Setup

Configure money-map. Arguments: `$ARGUMENTS`

## Steps
1. If a sample CSV is given, apply the `statement-parsing` skill to detect its column mapping and show it to the user to confirm.
2. Create `money/categories.json` from this plugin's `templates/categories.json` if it doesn't exist. Never overwrite an existing one without confirming.
3. Using the `categorization` skill, tailor the starter rules to what you see in the sample (add obvious merchant→category rules), and confirm with the user.
4. Tell the user they can edit `money/categories.json` anytime and commit it to share rules with a team.
5. Remind them: money-map reads only the files they provide and never connects to the internet or their bank.

Never access the network.
