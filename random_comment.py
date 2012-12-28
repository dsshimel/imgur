import urllib
import urllib2
import json
import string
import random
import math
from bs4 import BeautifulSoup
from httplib import BadStatusLine

GALLERY_PREFIX = 'http://imgur.com/gallery/'
MARKOV_LENGTH = 3
MAX_COMMENT_LENGTH = 140

def get_page_of_images(img_category, sort_by, page_num):
  req_url = GALLERY_PREFIX + img_category + '/' + sort_by + '/page/' + str(page_num) + '.json'
	response = urllib2.urlopen(urllib2.Request(req_url))
	return json.loads(response.read())

def get_image_comments_html(id, sort_by, inline):
	req_url = GALLERY_PREFIX + id + '/comment/' + sort_by + '/?inline=' + string.lower(str(inline))
	try:
		return urllib2.urlopen(urllib2.Request(req_url)).read()
	except BadStatusLine:
		return ''

def is_comment_tag(tag):
	return tag.name == 'div' and tag.has_key('class') and 'comment' in tag['class']
	
def is_root_comment_tag(tag):
	return is_comment_tag(tag) and tag.has_key('data-level') and tag['data-level'] == '0'

def is_empty_span(tag):
	return tag.name == 'span' and len(tag.attrs) == 0
	
def is_points_tag(tag):
	if tag.name != 'span' or not tag.has_key('class'):
		return False
	for c in tag['class']:
		if 'points-' in c and 'points-text-' not in c:
			return True
	return False

def create_markov_matrix(matrix, start_words, words):
	added_start_word = False
	while len(words) > MARKOV_LENGTH:
		part = words[:MARKOV_LENGTH]
		chain = ''
		for index, word in enumerate(part):
			chain += word + ' '
		chain = chain.strip()
		if not added_start_word:
			start_words.append(chain)
			added_start_word = True
		assert len(chain.split()) == MARKOV_LENGTH
		if chain in matrix:
			length = len(matrix[chain])
			matrix[chain].append(words[MARKOV_LENGTH])
			assert len(matrix[chain]) == length + 1
		else:
			matrix[chain] = [words[MARKOV_LENGTH]]
			assert len(matrix[chain]) == 1, text
		words.pop(0)
	return matrix

def get_random_index(collection):
	return int(math.floor(random.random() * len(collection)))
	
def make_markov_comment(matrix, start_words):
	key = start_words[get_random_index(start_words)]
	comment = key + ' '
	while key in matrix:
		next_words = matrix[key]
		next_word = next_words[get_random_index(next_words)]
		if len(comment + next_word) <= MAX_COMMENT_LENGTH:
			comment += next_word + ' '
			split_key = key.split()
			assert len(split_key) == MARKOV_LENGTH
			key = ''
			for keyword in split_key[1:]:
				key += keyword + ' '
			key += next_word
		else:
			break
	return comment.strip()
	
image_json = get_page_of_images('hot', 'time', 0)
matrix = {}
actual_comments = {}
start_words = []
num_images = len(image_json['data'])
image_ctr = 1
for image in image_json['data']:
	id = image['hash']
	comments_html = get_image_comments_html(id, 'top', True)	
	soup = BeautifulSoup(comments_html)
	comment_divs = soup.find_all(is_root_comment_tag)
	for comment in comment_divs:
		points_spans = comment.find_all(is_points_tag)
		points = int(points_spans[0].string.replace(',', '')) # these are the point spans for the highest-level (root) comments
		if points < 2:
			continue
		spans = comment.find_all(is_empty_span)
		root_comment_span = spans[0] # root-level comment spans
		comment_text = root_comment_span.get_text().strip()
		actual_comments[comment_text] = id
		matrix = create_markov_matrix(matrix, start_words, comment_text.split())
	print 'processed ' + str(image_ctr) + ' of ' + str(num_images) + ' images'
	image_ctr += 1

while True:
	comment = make_markov_comment(matrix, start_words).encode('utf-8')
	if comment not in actual_comments and len(comment.split()) > MARKOV_LENGTH + 1:
		print comment
