import collections
import datetime
import pygal
import numpy as np
import os
import praw
import pyimgur
import requests
import string
import time

# MAKE THIS PROGRAM DISTINGUISH BETWEEN WORDS AND PHRASE COUNT

class rdata_bot():
  
	def __init__(self, subreddits, words):
		self.r = praw.Reddit('this is /u/swingtheory\'s data gatherer!')
		self.r.login("username", 'password')
		self.subreddit_names = subreddits
		self.subreddit_list = [self.r.get_subreddit(x) for x in subreddits]
		self.key_words = words

	def run(self):
		for i, subreddit in enumerate(self.subreddit_list):
			# gets the top submissions in the past week
			top_submissions = list(subreddit.get_top_from_week(limit=20))

			word_occurences = self.count_occurrences(top_submissions)
			# plot results in .svg file 
			self.plot_results(self.subreddit_names[i], word_occurences)
	
	# counts the occurences of specified words in entire subreddit
	def count_occurrences(self, submissions):

		phrase_occurrences = collections.Counter()

		print('len submissions', len(submissions))
		for i, submission in enumerate(submissions):
			print('submission #' + str(i+1))
			submission.replace_more_comments(limit=2)
			submission_comments = praw.helpers.flatten_tree(submission.comments)
			comments_searched = set()
			print('length sub comments:', len(submission_comments))
			for comment in submission_comments:
				if comment.id not in comments_searched:
					for key_word in self.key_words:
						comment_text = comment.body.lower()
						if key_word in comment_text.translate(str.maketrans("","",string.punctuation)).split():
							phrase_occurrences[key_word] += comment_text.count(key_word)
					comments_searched.add(comment.id)

		return phrase_occurrences.most_common()

	def plot_results(self, subreddit_name, phrase_counts):
		bar_chart = pygal.Bar()
		bar_chart.title = "Word Frequency in /r/"+subreddit_name

		# creates bar data
		for i, count in enumerate(phrase_counts):
			bar_chart.add(count[0], count[1])

		save_folder = os.path.join(os.getcwd(), 'data_bot_output')
		# checks if path exists
		if not os.path.exists(save_folder):
			os.makedirs(save_folder)

		# saves file
		print("Saving figure to '%s'..." % save_folder)
		bar_chart.render_to_file(os.path.join(save_folder, subreddit_name+str(datetime.date.today())+'.svg'))

	# checks to see if string is a word to count
	def filter_word(self, word):
		if word.isdigit():
			return None
		if len(word) < 4:
			return None
		if word in self.ignore:
			return None	

		return word.lower()


if __name__ == '__main__':

	# specify words to search for
	key_words = [
		"hate",
		"love",
		"isis",
		"republicans",
		"democrats",
		"vote",
		"florida",
		"dc",
		"money",
		"power"
		]
	# specify the subredditname only, omit the /r/
	subreddit_list = [ 
		'worldnews', 
		'news', 
		'politics', 
		'worldpolitics'
		]

	data_bot = rdata_bot(subreddit_list, key_words)
	data_bot.run()

