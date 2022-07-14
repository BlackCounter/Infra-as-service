# Maintainer: Ganriele Giorgetti <g.giorgetti@gmail.com>
pkgname=rduty
pkgver=0.3.2
pkgrel=1
epoch=
pkgdesc="A simple and quick program to execute and automate remote commands"
arch=(x86_64 i386)
url="https://github.com/gabgio/rduty/releases/download/v0.3.2/rduty-0.3.2.tar.gz"
license=('GPL2')
groups=()
depends=('python3')
checkdepends=(python3)
options=()
source=("https://github.com/gabgio/rduty/releases/download/v$pkgver/$pkgname-$pkgver.tar.gz")

build() {
	cd "$pkgname-$pkgver"
	make PREFIX=/usr
}

package() {
	cd "$pkgname-$pkgver"
	make PREFIX="$pkgdir/usr" install
}
md5sums=('548a8df10bfd7114298696c07b361336')
