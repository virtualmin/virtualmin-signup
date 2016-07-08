use Test::Strict tests => 3;                      # last test to print

syntax_ok( 'confirm.cgi' );
strict_ok( 'confirm.cgi' );
warnings_ok( 'confirm.cgi' );
