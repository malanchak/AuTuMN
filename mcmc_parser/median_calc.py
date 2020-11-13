import pandas as pd
import numpy as np
import scipy.stats as st
import math

def main():
	csv_file = "output_mcmc.csv"
	df = pd.read_csv(csv_file,sep=",") # reads .csv as a pandas dataframe

	columns2evaluate = [column for column in df.columns if column not in ['idx','Scenario','accept']] # remove unnecessary features

	for column in columns2evaluate:
		print("Column:\t{}".format(column))
		print("Mean:\t{}".format(np.mean(df[column])))
		print("95% CI {}".format(st.t.interval(0.95, len(df[column])-1, loc=np.mean(df[column]), scale=st.sem(df[column]))))
		print("Median:\t{}".format(np.median(df[column])))
		print("STD:\t{}".format(np.std(df[column])))
		print("25%:\t{}".format(np.percentile(df[column],25)))
		print("50%:\t{}".format(np.percentile(df[column],50)))
		print("75%:\t{}".format(np.percentile(df[column],75)))
		print("\n")
	return True
	
if __name__ == "__main__":
	main()