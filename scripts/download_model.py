from argparse import ArgumentParser
from pathlib import Path

from huggingface_hub import snapshot_download

if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument(
		"--model_name_or_path",
		type=str,
		required=True,
		help="Path to pretrained model or model identifier from huggingface.co/models",
	)
	parser.add_argument("--output_dir", type=str, required=True, help="Path to output dir")
	# init args
	args = parser.parse_args()
	local_path = Path(args.output_dir)
	model_name = args.model_name_or_path
	snapshot_download(
		model_name,
		local_dir=local_path.joinpath(model_name),
		force_download=True,
		revision="main",
	)
