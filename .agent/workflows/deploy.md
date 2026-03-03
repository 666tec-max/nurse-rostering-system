---
description: Push all local changes to GitHub (auto-deploys to Streamlit Cloud)
---

# Deploy to GitHub

This workflow commits and pushes all local changes to the GitHub repository.
Streamlit Community Cloud will automatically redeploy the app after the push.

**Repository:** https://github.com/666tec-max/nurse-rostering-system
**Live App:** https://test-roster-system.streamlit.app/

## Steps

// turbo-all

1. Stage all changes:
```bash
cd /Users/tec/Documents/trae_projects/3 && git add -A
```

2. Show what changed:
```bash
cd /Users/tec/Documents/trae_projects/3 && git status
```

3. Commit with a descriptive message summarizing the changes:
```bash
cd /Users/tec/Documents/trae_projects/3 && git commit -m "<descriptive message based on changes>"
```

4. Push to GitHub:
```bash
cd /Users/tec/Documents/trae_projects/3 && git push origin main
```

5. Confirm the push was successful and inform the user that Streamlit Cloud will auto-redeploy within a minute or two. Provide the live app URL: https://test-roster-system.streamlit.app/
