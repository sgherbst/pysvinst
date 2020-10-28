`ifdef MUX1
module mux1
`elsif MUX2
module mux2
`endif
#(
    parameter DATA_WIDTH = 1
)
(
    input sel,
    input [(DATA_WIDTH-1):0] in0,
    input [(DATA_WIDTH-1):0] in1,
    output [(DATA_WIDTH-1):0] out
);
    assign out = sel ? in1 : in0;
endmodule