# About

In this file the following documentations will be given:

* Explanation of the code I wrote in the project
* How to run the code I wrote in the project

## My code in the project

My work was based on the DiscoPygal we've got from the
course's staff at assignment 4.<br />
There exists a pull request in the repo
which you can always look at
([pull request](https://github.com/TomerEpshtein/robotics_project/pull/1))
in order to see all the differences between 
the base version and my version.

#### RRT*

I implemented the RRT* star algorithm.
The implementation is in the path mrmp/solvers/rrt_star/ .
Under this folder there exists all the relevant files
to RRT* solver which I'll explain about:

1. <em/>random_points_in_polygon_generator.py -<br />
    In this file the responsibility for generating 
   points in the room is implemented.
2. <em/>nearest_point_search.py -<br/>
    In this file the responsibility for finding 
   nearest neighbors in RRT* is implemented.
3. <em/>rrt_star.py -<br />
    In this file the RRT* algorithm is implemented.<br />
    As you can see, in the method *get_path* in the file, 
   the pseudo-code of RRT* is implemented.
4. <em/>solver.py-<br/>
   This file is used in order to run the RRT*,
   it uses the previous files in order to calculate
    the path.

#### My extension to PRM

I implemented an extension to the PRM discs algorithm.
The implementation is in the path mrmp/solvers/my_algo .
 this folder there exists the relevant files
which I'll explain about:

1. <em/>local_prm_discs.py -<br />
   This file contains the local prm algorithm implementation.
2. <em/>prm_2_minlen.py -<br/>
    This file is used in order to run my extension.

#### Scenes

Under the mrmp/scenes folder which was already exists,
I added 100 scenes files which I created and called them
1.json, 2.json, ... , 100.json .