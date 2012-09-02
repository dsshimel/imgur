import urllib
import re

IMAGE_URL_PREFIX = 'http://imgur.com/gallery/'
LINK_PREFIX = '<a href="' + IMAGE_URL_PREFIX
LINK_MIDDLE = '">'
LINK_SUFFIX = '</a>'

def get_new_imgur_text(url):
	imgur = urllib.urlopen(url)
	text = imgur.read()
	imgur.close()
	return text.split("\n")

imgur_url = 'http://imgur.com/gallery/new'
html_lines = get_new_imgur_text(imgur_url)

# find the outer div just before where the individual images start
posts_start_idx = -1
for i in range(0, len(html_lines)):
	if html_lines[i].find('<div class="posts">') != -1:
		posts_start_idx = i
		break
		
# couldn't find where the posts start, probably didn't get the page in the correct format
if posts_start_idx == -1:
	print html_lines
	exit()
		
# find the closing div tag to the above div
posts_end_idx = -1
for i in range(posts_start_idx, len(html_lines)):
	if html_lines[i].find('<div class="clear"></div>') != -1:
		posts_end_idx = i + 1
		break
		
# regexes for identifying a post DOM element and for identifying a points DOM element, respectively
post_regex = re.compile('<div id="(\w\w\w\w\w)" class="post">')
points_regex = re.compile("<span class='points-(\w\w\w\w\w)'>([0-9]+)</span>")

image_id_to_points = {}
for i in range(posts_start_idx, posts_end_idx):
	line = html_lines[i]
	post_match = post_regex.search(line)
	if post_match:
		image_key = post_match.group(1)
		for j in range(i + 1, i + 11): # eyeballing the range here, but it works
			points_match = points_regex.search(html_lines[j])
			if points_match:
				if points_match.group(1) != image_key: # ensure that we picked the points element that corresponds to current post
					exit(points_match.group(1) + ' did not match ' + image_key)
				else:
					image_id_to_points[image_key] = int(points_match.group(2))
					break

# sort the posts by points, lowest to highest
sorted_by_points = list(sorted(image_id_to_points, key=image_id_to_points.__getitem__, reverse=False))

output_file = open('imgur_links.html', 'w+')

# print out a series of basic HTML statements to get all the links in one place
for key in sorted_by_points:
	points = str(image_id_to_points[key])
	line = LINK_PREFIX + key + LINK_MIDDLE + key + ': ' + points + LINK_SUFFIX + '<br>'
	#print LINK_PREFIX + key + LINK_MIDDLE + key + ': ' + points + LINK_SUFFIX + '<br>'
	output_file.write(line + "\r\n")

output_file.close()