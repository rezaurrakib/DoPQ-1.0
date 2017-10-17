##############################
# Dockerfile for running python tasks with Tensorflow-GPU support
################
# VERSION               0.1.1
# ##
#

FROM corresive/tfbase:latest
LABEL version="0.1.1"
LABEL description="Dockerfile for running python tasks with Tensorflow-GPU support"
LABEL maintainer="Markus.Rohm@med.lmu.de"

# create directories
RUN mkdir /home/deepdive
RUN mkdir /home/deepdive/input_data

# copy run files
COPY run_task.sh /home/deepdive
COPY task.py /home/deepdive
COPY input_data/t10k-images-idx3-ubyte.gz /home/deepdive/input_data
COPY input_data/t10k-labels-idx1-ubyte.gz /home/deepdive/input_data
COPY input_data/train-images-idx3-ubyte.gz /home/deepdive/input_data
COPY input_data/train-labels-idx1-ubyte.gz /home/deepdive/input_data

WORKDIR "/home/deepdive"

# TensorBoard
EXPOSE 6006
# IPython
EXPOSE 8888

CMD ["/home/deepdive/run_task.sh", "--allow-root"]

