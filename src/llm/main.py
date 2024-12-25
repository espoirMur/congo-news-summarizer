import argparse

from src.llm.runner import run as run_summarization

parser = argparse.ArgumentParser()

# this file should run only today
if __name__ == "__main__":
	prompt = "You are a french news reporter"
	parser.add_argument("-e", "--environment", default="dev")
	parser.add_argument("-s", "--save_to_s3", default=False)
	parser.add_argument("-f", "--file_name", default=None)
	parser.add_argument("-d", "--day_ago", default=0, type=int)
	args = parser.parse_args()
	run_summarization(
		environment=args.environment,
		save_to_s3=args.save_to_s3,
		file_name=args.file_name,
		day_ago=args.day_ago,
	)
