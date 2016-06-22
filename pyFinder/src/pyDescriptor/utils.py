import urllib.request
import json
import docker
import sys

# get ingo of image (pull, stars, last updated, description
#https://hub.docker.com/v2/repositories/senorgdev/docker-images


def get_all_tags(repo_name, page_size=50):

    """
    "count": 256,
    "next": null,
    "previous": "https://hub.docker.com/v2/repositories/library/java/tags/?page=25",
    "results": [ {
        "name": "openjdk-6b34",
        "full_size": 418425609,
        "id": 22107,
        "repository": 21373,
        "creator": 7,
        "last_updater": 7,
        "last_updated": null,
        "image_id": null,
        "v2": false,
        "platforms": []
     } ]
    """

    url_tags = "https://hub.docker.com/v2/repositories/" + repo_name + "/tags/?page=1&page_size=" + str(page_size)
    #https: // hub.docker.com / v2 / repositories / senorgdev / docker - images / tags /?page = 1 & page_size = 100
    json_response = req_to_json(url_tags)
    print("["+repo_name+"] tags founds " + str(json_response['count']))
    list_tags = []
    if json_response['count'] > 0:
        next = ""
        while next is not None:
            json_list_tags = json_response['results']
            list_tags = list_tags + [res['name'] for res in json_list_tags]
            next = json_response['next']
    return list_tags


def req_to_json(url):
    response = urllib.request.urlopen(url).read()
    json_response = json.loads(response.decode())
    return json_response


def pull_image(repo_name, tag="latest"):
    # sets the docker host from your environment variables
    client = docker.Client(**docker.utils.kwargs_from_env(assert_hostname=False))
    # try to set image
    if not repo_name:
        ims = client.images()
        if len(ims) >= 1:
            repo_name = [im['RepoTags'][0] for im in client.images()][0]

    assert repo_name, 'No image given or found locally.'

    # get image if not available locally
    im_names = [im['RepoTags'][0] for im in client.images()]  # all the images in the host (first tag)

    if (not any([repo_name in imname for imname in im_names])) and client.search(
            repo_name):  # not found locally and found remote
        print('Image {} not found locally. Pulling from docker hub.'.format(repo_name))
        for line in client.pull(repo_name, tag, stream=True):
            print(line.decode())


def remove_image(image, force=False):
    client = docker.Client(**docker.utils.kwargs_from_env(assert_hostname=False))
    print('Removing {} form local docker'.format(image))
    try:
        client.remove_image(image,force)
    except:
        e = sys.exc_info()[0]
        print(e)