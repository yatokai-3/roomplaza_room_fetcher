# roomplaza_room_fetcher
fetch the latest listings from delft, hague and rotterdam (condition, from 1-Aug,2026 & tenant = 4)

 ---
# Key behaviour summary

## 1. 🌉 {city}_final.json 

- ALWAYS matches the current website 
- Old listings removed automatically 

## 2. 🏠 {city}_seen_ids.json

- Only grows & keeps track of all listings even after they are not present on the website.
- Never removes anything 

 ---
 # To add new emails as cc follow these steps.

 1. Add a new secret in GitHub → (key_name) CC_EMAILS → (value:) friend1@gmail.com,friend2@gmail.com
 2. In .yml file pass this -> CC_EMAILS: ${{ secrets.CC_EMAILS }}
 3. and finally update the _rp.py code,

``` python 
cc = os.environ.get("CC_EMAILS", "").split(",")

resend.Emails.send({
    "from":    "onboarding@resend.dev",
    "to":      os.environ["NOTIFY_EMAIL"],
    "cc":      [x for x in cc if x],   # filters out empty strings
    "subject": f"🏠 {total} new RoomPlaza listing(s)!",
    "html":    html,
})
