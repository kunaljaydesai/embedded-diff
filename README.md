# Embedded Git Diffs

You might be wondering why are embedded git diffs useful. The use case I had was to be able to show code diffs when writing tutorial blog posts, that way its easier to see how code is evolving over the course of the tutorial.

# Setup

1. Run `virtualenv env`
2. Run `source env/bin/activate`
3. Run `pip install -r requirements.txt`
4. Run `GH_TOKEN="<your-token-here>" flask --debug run`
