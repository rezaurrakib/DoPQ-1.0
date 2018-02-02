# DoP-Q
## Queue for docker to run projects on a multi-gpu machine ##

__History:__
+ 12.10.2017: Initial commit.
+ 16.10.2017: Changed to python 2.7
+ 31.01.2018: Refactored queue from the ground up. Introduced modules builder.py, container_handler.py, gpu_handler.py and helper_process.py

_HowTo get started:_
> Just download run\_python\_script in examples/simple and zip the content of the folder. Name it to "build\_\[SOME\_NAME\]\_\[YOUR\_NAME].zip", where \[SOME\_NAME\] is some name you may freely choose and where \[YOUR\_NAME] represents your username. Copy it to the container.path directory of the queue and it will be built and run automatically. Please not that \[YOUR\_NAME\] must be authorized to run docker files on the machine. Please speak to some administrator of the machine (Ilja Manakov, Markus Rohm).
