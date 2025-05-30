# update system
apt update
apt upgrade -y
# install Linux tools and Python 3 libs
apt install -y software-properties-common python3-dev python3-pip python3-wheel python3-setuptools
# install Python packages
python3 -m pip install --upgrade pip

curl -sSL https://install.python-poetry.org | python3 -