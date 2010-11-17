var list = ["a",1,2,3,"foo"];
var dict = {"abc":123, "foo":"bar"};

// Must be true
var x = "a" in list;
var y = "abc" in dict;

// Must be false
var a = "bar" in list;
var b = "asdf" in dict;
