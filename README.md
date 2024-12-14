Congratulations! Your new Hugo site was created in D:\Static-Site-Generators\HUGO\bluebook.

Just a few more steps...

1. Change the current directory to D:\Static-Site-Generators\HUGO\bluebook.
2. Create or install a theme:
   - Create a new theme with the command "hugo new theme <THEMENAME>"
   - Or, install a theme from https://themes.gohugo.io/
3. Edit hugo.yaml, setting the "theme" property to the theme name.
4. Create new content with the command "hugo new content <SECTIONNAME>\<FILENAME>.<FORMAT>".
5. Start the embedded web server with the command "hugo server --buildDrafts".

See documentation at https://gohugo.io/.


### Setup
- Make a GForm and put the Form-To-PR-AppScript.js put GH_TOKEN properties, set a new form submit trigger
- Make another AppScript at https://script.google.com/ and put Gmail-To-Proxy-Emails-And-Regex-AppScript.js put GH_TOKEN and FORM_ID as properties, set a time based trigger
- Setup on the mail id a filter that stars messages with academic email regex and labels them something
- For GH_Workflows make a PAT secret too
