from app import app
from copy import deepcopy
from flask import Flask, render_template, flash, redirect, url_for
import numpy as np
from .forms import LoginForm
from textwrap import wrap

import matplotlib.pyplot as plt
plt.switch_backend('agg')
import os

import sys
sys.path.append('../code/')
import lstm2

def generate_png(predicted_df, stock, days, index_fund_pct_gain):
	column = str(days) + '-day prediction'
	actual_col = str(days) + '-day actual'
	predicted_gains = deepcopy(predicted_df[stock])
	predicted_gains['Predicted Gain'] = 100*(predicted_gains[column] - predicted_gains['current price'])/predicted_gains['current price']
	predicted_gains['Actual Gain'] = 100*(predicted_gains[actual_col] - predicted_gains['current price'])/predicted_gains['current price']
	predicted_gains['S&P500 Index Gain'] = index_fund_pct_gain
	to_plot = predicted_gains[['Predicted Gain', 'Actual Gain', 'S&P500 Index Gain']]
	#print(to_plot)
	title_text = "Predicted and Actual returns to " + stock +" after holding for " + str(days) + " days during the previous quarter"

	ax = to_plot.plot()
	ax.set_title("\n".join(wrap(title_text, 60)))
	# mean = predicted_df[stock][column].mean()
	# std = predicted_df[stock][column].std()
	#ax.axhline(y=mean,color = 'k', ls='--', lw=0.5, label=column + ' mean')
	#ax.axhline(y=mean+std,color = 'b', ls='-.', lw=0.5, label=column + ' + std')
	#ax.axhline(y=mean-std,color = 'b', ls='-.', lw=0.5, label=column + ' - std')
	ax.set_xlabel("Day")
	ax.set_ylabel('Percent gain over ' + str(days) + ' days')
	ax.legend()

	fig = ax.get_figure()
	stock_png = 'static/%s_%s.png' % (stock, days)
	fig.savefig('app/' + stock_png)
	print('generate_png', stock_png)
	plt.close(fig)

	return '/' + stock_png

def get_image_key(stock, days):
	return "%s_%s" % (stock,days)


def run_model(days, risk):
	'''
	Hook this into the algorithm to return the predicitons associated with given amount, returns and tolerance
	inputs: the amount ($), 30/45/60 for the days, and low/medium/high for risk level
	outputs: recommended and alternative stock pick, graphs for each of them
	'''
	print(days, risk)

	summary_df, predicted_df = lstm2.recommend_stocks(days, risk)
	print(summary_df)
	stock1 = summary_df['Stock Model'].iloc[0]
	rmse1 = summary_df['rsme'].iloc[0]
	stock2 = summary_df['Stock Model'].iloc[1]
	rmse2 = summary_df['rsme'].iloc[1]

	top_10 = summary_df.head(10)
	images = {}

	sp500_index_gain = lstm2.read_index_fund(days)
	# Generates all images
	for index, row in top_10.iterrows():
		stock = row['Stock Model']
		key = get_image_key(stock, days)
		images[key] = generate_png(predicted_df, stock, days, sp500_index_gain)

	png1 = images[get_image_key(stock1, days)]
	png2 = images[get_image_key(stock2, days)]

	#print(stock1, stock2, png1, png2)
	print(type(sp500_index_gain))
	return stock1, rmse1, png1, stock2, rmse2, png2, top_10, "%.2f" % np.mean(sp500_index_gain)


@app.route('/background', methods=['POST', 'GET'])
def background():
	form = LoginForm()
	if form.validate_on_submit():
		return redirect(url_for('main_form'))
	else:
		return render_template('background.html', form=form)
@app.route("/testing")
def example():
	return redirect(url_for('main_form'))

@app.route('/', methods=['POST', 'GET'])
def main_form():
	form = LoginForm()
	if form.validate_on_submit():
		stock, stock_rmse, stock_plot, alt, alt_rmse, alt_plot,summary_df, index_avg_gain = run_model(int(form.date.data),
													 form.risk_tolerance.data)
		return render_template('recommendation.html',form=form,
			date = str(form.date.data), risk = form.risk_tolerance.data, main_rmse = stock_rmse,
			plot_name=stock_plot, alternative_plot_name=alt_plot, recommended = stock, alternate = alt, alternate_rmse = alt_rmse,
			dataframe=summary_df.to_html(index=False), sp500_index_avg_gain = index_avg_gain,
			df_json=summary_df.reset_index().to_json(orient='records'))

	print(form.date.data, form.risk_tolerance.data)
	return render_template('recommendation.html',form=form, date = "__", risk = "__", main_rmse = '__',
			plot_name="/static/question.png", 
			alternative_plot_name="/static/question.png",
			alternate_rmse = '__', sp500_index_avg_gain = None,
			dataframe=None, df_json=None
			)









