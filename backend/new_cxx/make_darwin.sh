export PUMA_PATH=/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/venture/puma
make
sudo mv -f libtrace.dylib $PUMA_PATH/libtrace.so
