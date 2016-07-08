use Test::Strict tests => 3;                      # last test to print

syntax_ok( 'captcha.cgi' );
strict_ok( 'captcha.cgi' );
warnings_ok( 'captcha.cgi' );
