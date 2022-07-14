#!/usr/bin/make -s

PACKAGE=rduty
VERSION=0.4.1

# install architecture-independent files
PREFIX=/usr/local
# system admin executables
BINDIR=$(PREFIX)/bin

DIST=\
	AUTHORS			\
	LICENSE			\
	CHANGELOG.rst	\
	Makefile		\
	README.rst		\
	INSTALL.rst		\
	src/rduty.py

src/$(PACKAGE): src/$(PACKAGE).py
	@cp src/$(PACKAGE).py src/$(PACKAGE)
	@echo "Type 'make install' to install $(PACKAGE)"

	
all: src/$(PACKAGE)

clean:
	rm -f *~
	rm -f src/*~
	rm -f src/*pyc
	rm -f src/$(PACKAGE)
	
distclean: clean
	rm -f $(PACKAGE)-$(VERSION).tar.*
	rm -f $(PACKAGE)-$(VERSION)*.deb
	rm -rf debian
	rm -rf .install_prefix
	
distgz: distclean
	mkdir $(PACKAGE)-$(VERSION)
	cp --recursive --parents $(DIST) $(PACKAGE)-$(VERSION)
	tar -zcvf $(PACKAGE)-$(VERSION).tar.gz $(PACKAGE)-$(VERSION)
	rm -r $(PACKAGE)-$(VERSION)
	
distbz2: distclean
	rm -f *~
	mkdir $(PACKAGE)-$(VERSION)
	cp --recursive --perents $(DIST) $(PACKAGE)-$(VERSION)
	tar -jcvf $(PACKAGE)-$(VERSION).tar.bz2 $(PACKAGE)-$(VERSION)
	rm -r $(PACKAGE)-$(VERSION)

deb: distclean
	mkdir -p debian
	$(MAKE) PREFIX=/usr 
	$(MAKE) PREFIX=`pwd`/debian/usr install 
	
	mkdir -p debian/DEBIAN
	@echo "Package: $(PACKAGE)" > debian/DEBIAN/control
	@echo "Version: $(VERSION)-1" >> debian/DEBIAN/control
	@echo "Section: admin"  >> debian/DEBIAN/control
	@echo "Priority: optional"  >> debian/DEBIAN/control
	@echo "Architecture: all"  >> debian/DEBIAN/control
	@echo "Depends: python3 (>= 3)"  >> debian/DEBIAN/control
	@echo "Maintainer: Gabriele Giorgetti <g.giorgetti@gmail.com>"  >> debian/DEBIAN/control
	@echo "Description: A Python script to easily and quickly run a command or multiple commands on remote hosts."  >> debian/DEBIAN/control
	@echo "  This is a simple script written in Python which allows you to"                                           >> debian/DEBIAN/control
	@echo "  easily and quickly run a command or multiple commands on remote and local hosts and devices"             >> debian/DEBIAN/control
	@echo "  via ssh (telnet is also supported). It is also able to automate repetitive tasks on many hosts"     	    >> debian/DEBIAN/control
	@echo "  using inventory files from Ansible, or simple .ini inventory files."										>> debian/DEBIAN/control

	dpkg-deb --build debian
	mv debian.deb $(PACKAGE)-$(VERSION)-1_all.deb
	rm -r debian

dist: distgz

install: src/$(PACKAGE)
	@# creates directories
	install -d $(BINDIR)

	@# installs rduty
	install --mode 0755 src/$(PACKAGE) $(BINDIR)/$(PACKAGE)

	@# Write install prefix for the uninstall procedure
	@echo $(PREFIX) > .install_prefix

uninstall:
	if [ -f ".install_prefix" ]; \
	then \
		rm -f  $(shell cat .install_prefix)/bin/$(PACKAGE); \
		rm -f .install_prefix; \
	fi

