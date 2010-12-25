Number.prototype = "This is the new prototype";
Object.prototype.test = "bar";
Object = "asdf";
var x = Object.prototype;
x.test = "asdf";
