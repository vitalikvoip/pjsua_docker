### Builder
FROM debian:buster as builder
MAINTAINER Vitaliy Aleksandrov <vitalik.voip@gmail.com>

User root
ENV DEBIAN_FRONTEND noninteractive

WORKDIR /usr/local/src
RUN apt-get update
RUN apt-get install -y apt-utils procps net-tools python python-dev wget tar nano
RUN apt-get install -y build-essential git bison flex m4 pkg-config libncurses5-dev

RUN wget https://www.pjsip.org/release/2.9/pjproject-2.9.tar.bz2 && tar -xjf pjproject-2.9.tar.bz2

WORKDIR /usr/local/src/pjproject-2.9
RUN ./configure --prefix=/usr/local/pjsip CFLAGS='-g -fPIC' --enable-shared
RUN printf "export CFLAGS += -fPIC\nexport LDFLAGS +=\n" > user.mak
RUN make dep && make clean && make && make install
RUN cd pjsip-apps/src/python && make && make install
RUN echo "/usr/local/pjsip/lib" > /etc/ld.so.conf.d/pjsip.conf && ldconfig

### TestTool
FROM debian:buster as testtool
MAINTAINER Vitaliy Aleksandrov <vitalik.voip@gmail.com>

User root
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y apt-utils procps net-tools python nano libssl1.1

RUN mkdir -p /usr/local/lib/python2.7
COPY --from=builder /usr/local/lib/python2.7/dist-packages /usr/local/lib/python2.7/dist-packages

COPY --from=builder /usr/local/pjsip /usr/local/pjsip
COPY --from=builder /etc/ld.so.conf.d/pjsip.conf /etc/ld.so.conf.d/pjsip.conf
RUN ldconfig

RUN mkdir /home/tests

ARG CACHEBOOST=1
COPY tests/* /home/tests/

WORKDIR /home/tests

ENTRYPOINT ["tail", "-f", "/dev/null"]
