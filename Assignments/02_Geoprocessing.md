# 02. Geoprocessing

Create a dataset that expresses a narrative from part of your daily life, either now or in the past. This can be based on a mental map of your experience in New York / another city, based on geolocated map tracks (i.e. Google Maps history), or some other source. Based on the data type (point, line, polygon), consider how it would or could relate to other datasets that lend themselves to describing your mental image of the city- subway routes, the location of open space, your favorite coffee cart, etc. We will spend time in the next class relating these kinds of datasets together. 
- Use https://geojson.io/, https://play.placemark.io/, QGIS, or another software  to create your dataset
- **You must submit a GeoJSON file of your dataset, along with a proposed related dataset, via Github, along with a proposed workflow for relating the two (expressed as a diagram)**. Upload the file in the `Assignments` folder along with a markdown document with a link to the other dataset and the proposed methodology. Ideally the related dataset will be something you have access to, but if not, describe how you would propose creating it. Come prepared to discuss, we will talk through a couple of examples next class.

<br>


**Project Description**

As someone who doesn’t keep a regular journal or post frequently on social media, my initial idea was to extract temporal patterns from mobile app data—such as headphone volume history—to explore potential correlations between geographic noise levels and emotional response. However, I was quickly disappointed to find that due to iPhone’s strong privacy protection, very little historical data is retained or made accessible. :(

This led me to a new direction: photos. Each photo I take is embedded with rich geolocation metadata, and often tied to a specific mood or moment. I initially hoped to find patterns in the repetition of specific subjects photographed across different locations—but that search wasn’t fruitful. Instead, I pivoted to analyzing the frequency of my photo-taking as a proxy for how “interesting” I found each place.

I then chose to compare this spatial distribution of photo activity with two NYC Open Data sources:

Land value by tax lot – to investigate whether economically “valuable” spaces align with personal interest.

PLUTO land use data – to examine how different urban functions (residential, commercial, mixed-use, etc.) relate to what I perceive as interesting.

Through this, I hope to explore how personal perception of urban interest maps onto the city’s economic and functional geographies.