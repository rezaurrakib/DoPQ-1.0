##############################
# Dockerfile for running python tasks with Tensorflow-GPU support
################
# VERSION               0.1.1
# ##
#

FROM dbsifilmu/tfbase:latest
LABEL version="0.1.1"
LABEL description="Dockerfile for running python tasks with Tensorflow-GPU support"
LABEL maintainer="Markus.Rohm@med.lmu.de"

# create directories
RUN mkdir /home/deepdive

# copy run files
COPY run_task.sh /home/deepdive
COPY task.py /home/deepdive

WORKDIR "/home/deepdive"

# TensorBoard
EXPOSE 6006
# IPython
EXPOSE 8888

CMD ["/home/deepdive/run_task.sh", "--allow-root"]

