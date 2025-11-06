# third-party-edtech-scraping
A handful of scripts that use Selenium to pry out some very specific reports from uncooperative edtech websites

## Usage
The files in this repository are all highly specific to my own use case. Feel free to use them as a template, but login credentials, relevant html tags, and the like will all vary greatly from user to user.

## Options
### Infinite Campus
 - attendance_extract.py: Uses Campus's Data Export tool to produce a csv containing all of the school year's positive attendance entries, and then returns the average number of scholars that have attended each course in the last 30 days.
### Stride
 - gap_extract.py: Iterates through Stride's Class Gap Report pages for select schools in the district, extracting student-level results and combining them into a more centralized table of math and reading scores.