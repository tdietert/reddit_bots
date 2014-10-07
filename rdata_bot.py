import collections
import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
import praw
import pyimgur
import requests
import re
import time

# MAKE THIS PROGRAM DISTINGUISH BETWEEN WORDS AND PHRASE COUNT

class rdata_bot():
  
	def __init__(self, subreddits, words):
		self.r = praw.Reddit('this is /u/swingtheory\'s data gatherer!')
		self.r.login("bot-username-here", 'bot-password-here')
		self.subreddit_names = subreddits
		self.subreddit_list = [self.r.get_subreddit(x) for x in subreddits]
		self.key_words = words

	def run(self):
		for i, subreddit in enumerate(self.subreddit_list):
			# gets the top submissions in the past week
			top_submissions = list(subreddit.get_top_from_week(limit=50))

			word_occurences = self.count_occurrences(top_submissions)
			output_graph = self.plot_results(self.subreddit_names[i], word_occurences)
			save_dir = os.getcwd() + '/rdata_bot_data/'
			self.save_locally(output_graph, save_dir, self.subreddit_names[i])
	
	# counts the occurences of specified words in entire subreddit
	def count_occurrences(self, submissions):

		phrase_occurrences = collections.Counter()

		print('len submissions', len(submissions))
		for i, submission in enumerate(submissions):
			print('submission #' + str(i+1))
			submission.replace_more_comments(limit=5)
			submission_comments = praw.helpers.flatten_tree(submission.comments)
			comments_searched = set()
			print('length sub comments:', len(submission_comments))
			for comment in submission_comments:
				if comment.id not in comments_searched:
					for key_word in self.key_words:
						comment_text = comment.body.lower()
						if key_word in comment_text:
							phrase_occurrences[key_word] += comment_text.count(key_word)
					comments_searched.add(comment.id)

		return phrase_occurrences.most_common()

	def plot_results(self, subreddit_name, phrase_count):
		phrases = [phrase[0] for phrase in phrase_count]
		times_used = [phrase[1] for phrase in phrase_count]

		y_axis = np.arange(len(phrase_count)) + 0.5
		bar_height = 0.7
		opacity = 0.8

		output_graph = plt.barh(y_axis, times_used, height=bar_height,
				                alpha=opacity,
				                align='center',
				                color='g',
				                yerr=0)

		x_max = max(times_used) + 0.1*max(times_used)
		plt.xlim([0, x_max])
		#labeling the graph
		plt.xlabel('Times Used')
		plt.ylabel('Phrase')
		plt.title('Occurrence of specified phrases for /r/' + subreddit_name)
		plt.yticks(y_axis, phrases)

		max_usage = times_used[0]
		# labels the bars with respective word usage counts
		self.label_graph(output_graph, x_max)
		# makes errything pretty
		plt.tight_layout()
		return output_graph

	def label_graph(self, rects, x_max):
		for rect in rects:
			width = rect.get_width()
			xloc = width + float(.05*x_max)
			yloc = rect.get_y() + rect.get_height()/2.0
			clr = 'white'
			align = 'right'

			plt.text(xloc, yloc, str(width), ha=align, va='center')

	def save_locally(self, output_graph, save_dir, subreddit_name):
		if not os.path.exists(save_dir):
			os.makedirs(save_dir)
		 
		# The final path to save to
		savepath = os.path.join(save_dir, subreddit_name+str(datetime.date.today())+'.png')
		print("Saving figure to '%s'..." % savepath),	 
		# save the figure
		plt.savefig(savepath)
		# close it
		plt.close()

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
		'love',
		'hate',
		'obama',
		'ebola',
		'epidemic',
		'afraid',
		'scared',
		'excited',
		'happy',
		'sad'
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

