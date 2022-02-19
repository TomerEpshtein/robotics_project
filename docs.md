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

### RRT*

I implemented the RRT* star algorithm.
The implementation is in the path mrmp/solvers/rrt_star/ .
Under this folder there exists all the relevant files
to RRT* solver which I'll explain about:

1. <em>random_points_in_polygon_generator.py</em> -<br />
    In this file the responsibility for generating 
   points in the room is implemented.
2. <em>nearest_point_search.py</em> -<br/>
    In this file the responsibility for finding 
   nearest neighbors in RRT* is implemented.
3. <em>rrt_star.py</em> -<br />
    In this file the RRT* algorithm is implemented.<br />
    As you can see, in the method *get_path* in the file, 
   the pseudo-code of RRT* is implemented.
4. <em>solver.py</em> -<br/>
   This file is used in order to run the RRT*,
   it uses the previous files in order to calculate
    the path.

---
**Running**

You should select the scene you want to run RRT* about.
Then you should select the <em>solver.py</em> as the planner file.
No parameters should be given to this solver.


---

### My extension to PRM

I implemented an extension to the PRM discs algorithm.
The implementation is in the path mrmp/solvers/my_algo .
 this folder there exists the relevant files
which I'll explain about:

1. <em>local_prm_discs.py</em> -<br />
   This file contains the local prm algorithm implementation.
2. <em>prm_2_minlen.py</em> -<br/>
    This file is used in order to run my extension.

---
**Running**

You should select the scene you want to run the extension about.
Then you should select the <em>prm_2_minlen.py</em> as the planner file.

You must give parameter of how many *landmarks* the algorithm will create.
These must be a positive number, e.g. 300.
<br/>If you pass only the number of *landmarks*, then the default *chunk_size*
will be used is 4.

If you want to use other *chunk_size*, you should pass the parameter like:
<br/>
<p align="center">num_landmarks,chunk_size</p>

For example 300,5 means that the number of
*landmarks* will be 300
and *chunk_size* will be 5.

---

### Scenes

Under the mrmp/scenes folder which was already exists,
I added 100 scenes files which I created and called them
<em>1.json, 2.json, ... , 100.json</em>.

### Experiment files

All these files are in the root directory of the project. 

#### Script files

The main scripts I used for the experiments are:

1. <em>experiment_main.py</em> -<br />
   In this file I ran all the scenes I created with
    the algorithms with each parameter.

2. <em>results_analyzer.py</em> -<br />
    I used this script to analyze all the results
    I've got from the previous script.

#### Result files

The following files was created by the <em>experiment_main.py</em>
script:

1. <em>results.csv</em> - <br/>
   Contains all the lengths of the paths for each
    scene + algorithm + parameter (if exists one).
2. <em>times.csv</em> -<br/>
   Contains all the running times of the runs for each
    scene + algorithm + parameter (if exists one).

