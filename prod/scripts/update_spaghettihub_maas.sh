set -e

REPO_DIR="/tmp/maas-mirror"

# Clone if the directory doesn't exist
if [ ! -d "$REPO_DIR" ]; then
    git clone git@github.com:SpaghettiHub/maas.git "$REPO_DIR"
    cd "$REPO_DIR"
    git remote add lp https://git.launchpad.net/maas
    git remote update
fi

# Update and push changes
cd "$REPO_DIR"
git fetch lp
git fetch origin
git merge lp/master
git push origin master