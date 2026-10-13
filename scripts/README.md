# Training chart

`python scripts/update_training_chart.py` refreshes
`assets/images/training-distance.svg` using only the anonymous public weekly
distance summary at https://www.attackpoint.org/log.jsp/user_21269.
The image shows five weeks ending on Saturday, including the incomplete current
week. Totals sum the rounded distances displayed by Attackpoint. No credentials,
activity descriptions, GPS tracks, or other personal fields are stored.

The **Update training chart** GitHub Actions workflow runs daily at approximately
12:17 UTC and can also be run from the Actions tab. It commits a valid image and
explicitly requests a GitHub Pages build, because commits made by `GITHUB_TOKEN`
do not trigger Pages automatically. It uses the repository's existing branch
publishing configuration, with `contents: write` and `pages: write` permissions;
no additional secret is needed.

If the source is unavailable, private, stale, or has an unexpected format, the
workflow fails before changing the image. The last successful chart and its
visible update date remain on the site. GitHub may disable scheduled workflows
in public repositories after 60 days without repository activity; re-enable it
in Actions if necessary.

Run the data and failure-handling checks with:

```sh
python -B -m unittest discover -s scripts -p 'test_training_chart.py'
```
