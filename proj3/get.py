import requests
import json

res = requests.get('https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&site=stackoverflow')

for data in res.json()['items']:
    print(data['title'])
    #look to 'https://api.stackexchange.com/docs/questions' for exact headers to call data['header']

#general json format: 
'''
{
  "items": [
    {
      "tags": [
        "git",
        "branch"
      ],
      "owner": {
        "account_id": 3681913,
        "reputation": 166,
        "user_id": 3066687,
        "user_type": "registered",
        "profile_image": "https://i.sstatic.net/9Wmik.png?s=256",
        "display_name": "aRBee",
        "link": "https://stackoverflow.com/users/3066687/arbee"
      },
      "is_answered": true,
      "view_count": 56,
      "answer_count": 3,
      "score": 0,
      "last_activity_date": 1782843986,
      "creation_date": 1782416676,
      "question_id": 79967023,
      "content_license": "CC BY-SA 4.0",
      "link": "https://stackoverflow.com/questions/79967023/git-in-azure-devops-list-branches-that-have-not-been-merged-into-main-branch",
      "title": "Git in Azure DevOps - List branches that have not been merged into main branch"
    },

    ...

    "some_itms" : {}
}
'''

