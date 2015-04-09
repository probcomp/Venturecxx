# Copyright (c) 2014 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

boot2docker up
boot2docker ip
boot2docker ssh "
cd $(pwd)
if [ ${PWD##*/} = 'windows' ]; then
    cd ../..
fi

echo 'Visit http://192.168.59.103:8888/ in your browser to see example notebooks'

source script/run_docker_container

echo 'Press enter to continue...'
read -n1 -s
"