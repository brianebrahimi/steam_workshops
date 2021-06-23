import re

workshop_comment_links = []
with open("../../output/workshop.txt") as f, open("../../output/workshop_comment_links.txt", 'w') as write:
	for line in f.readlines():
		m = re.findall(r'\d+', line)
		m = "".join(m)
		workshop_comment_links.append(m)
	for line in workshop_comment_links:
		write.write("https://steamcommunity.com/sharedfiles/filedetails/comments/" + line + '\n')