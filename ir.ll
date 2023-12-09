; ModuleID = "./vector_example.pop"
target triple = "unknown-unknown-unknown"
target datalayout = ""

%"Vector_struct_tmp_MMAANNGGLLEE_i32" = type {i32*, i32, i32}
declare i32 @"printf"(i8* %".1", ...)

declare i8* @"malloc"(i64 %".1")

declare i8* @"realloc"(i8* %".1", i64 %".2")

declare void @"memcpy"(i8* %".1", i8* %".2", i64 %".3")

declare void @"free"(i8* %".1")

@"null" = global i8 0
define i32 @"test"(i32 %"num")
{
entry:
  %".114" = alloca [25 x i8]
  %".78" = alloca [17 x i8]
  %".52" = alloca [17 x i8]
  %".26" = alloca [17 x i8]
  %".12" = alloca [14 x i8]
  %"vec" = alloca %"Vector_struct_tmp_MMAANNGGLLEE_i32"
  ; OP::define(stack) START
  ; OP::define(stack) END
  ; OP::call START
  ; OP::index START
  %".7" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"vec", i32 0
  ; OP::index END
  call void @"Vector_struct_tmp_MMAANNGGLLEE_i32_memberfunction_init"(%"Vector_struct_tmp_MMAANNGGLLEE_i32"* %".7")
  ; OP::call end
  ; OP::cast START
  store [14 x i8] c"Init called.\0a\00", [14 x i8]* %".12"
  %".14" = bitcast [14 x i8]* %".12" to i8*
  ; OP::cast END
  ; OP::call START
  %".17" = call i32 (i8*, ...) @"printf"(i8* %".14")
  ; OP::call end
  ; OP::call START
  ; OP::index START
  %".21" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"vec", i32 0
  ; OP::index END
  call void @"Vector_struct_tmp_MMAANNGGLLEE_i32_memberfunction_push"(%"Vector_struct_tmp_MMAANNGGLLEE_i32"* %".21", i32 10)
  ; OP::call end
  ; OP::cast START
  store [17 x i8] c"push %i, len %i\0a\00", [17 x i8]* %".26"
  %".28" = bitcast [17 x i8]* %".26" to i8*
  ; OP::cast END
  ; OP::call START
  ; OP::index START
  %".32" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"vec", i32 0
  ; OP::index END
  %".34" = call i32 @"Vector_struct_tmp_MMAANNGGLLEE_i32_memberfunction_get"(%"Vector_struct_tmp_MMAANNGGLLEE_i32"* %".32", i32 0)
  ; OP::call end
  ; OP::index START
  %".37" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"vec", i32 0, i32 2
  ; OP::index END
  ; OP::dereference START
  %".40" = load i32, i32* %".37"
  ; OP::dereference END
  ; OP::call START
  %".43" = call i32 (i8*, ...) @"printf"(i8* %".28", i32 %".34", i32 %".40")
  ; OP::call end
  ; OP::call START
  ; OP::index START
  %".47" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"vec", i32 0
  ; OP::index END
  call void @"Vector_struct_tmp_MMAANNGGLLEE_i32_memberfunction_push"(%"Vector_struct_tmp_MMAANNGGLLEE_i32"* %".47", i32 7878)
  ; OP::call end
  ; OP::cast START
  store [17 x i8] c"push %i, len %i\0a\00", [17 x i8]* %".52"
  %".54" = bitcast [17 x i8]* %".52" to i8*
  ; OP::cast END
  ; OP::call START
  ; OP::index START
  %".58" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"vec", i32 0
  ; OP::index END
  %".60" = call i32 @"Vector_struct_tmp_MMAANNGGLLEE_i32_memberfunction_get"(%"Vector_struct_tmp_MMAANNGGLLEE_i32"* %".58", i32 1)
  ; OP::call end
  ; OP::index START
  %".63" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"vec", i32 0, i32 2
  ; OP::index END
  ; OP::dereference START
  %".66" = load i32, i32* %".63"
  ; OP::dereference END
  ; OP::call START
  %".69" = call i32 (i8*, ...) @"printf"(i8* %".54", i32 %".60", i32 %".66")
  ; OP::call end
  ; OP::call START
  ; OP::index START
  %".73" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"vec", i32 0
  ; OP::index END
  call void @"Vector_struct_tmp_MMAANNGGLLEE_i32_memberfunction_push"(%"Vector_struct_tmp_MMAANNGGLLEE_i32"* %".73", i32 26)
  ; OP::call end
  ; OP::cast START
  store [17 x i8] c"push %i, len %i\0a\00", [17 x i8]* %".78"
  %".80" = bitcast [17 x i8]* %".78" to i8*
  ; OP::cast END
  ; OP::call START
  ; OP::index START
  %".84" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"vec", i32 0
  ; OP::index END
  %".86" = call i32 @"Vector_struct_tmp_MMAANNGGLLEE_i32_memberfunction_get"(%"Vector_struct_tmp_MMAANNGGLLEE_i32"* %".84", i32 2)
  ; OP::call end
  ; OP::index START
  %".89" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"vec", i32 0, i32 2
  ; OP::index END
  ; OP::dereference START
  %".92" = load i32, i32* %".89"
  ; OP::dereference END
  ; OP::call START
  %".95" = call i32 (i8*, ...) @"printf"(i8* %".80", i32 %".86", i32 %".92")
  ; OP::call end
  ; SCOPE::if START
  ; OP::index START
  %".101" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"vec", i32 0, i32 2
  ; OP::index END
  ; OP::dereference START
  %".104" = load i32, i32* %".101"
  ; OP::dereference END
  ; OP::less_than START
  %".107" = icmp slt i32 %".104", 100
  ; OP::less_than END
  ; internal::cbranch_position
  br i1 %".107", label %".98", label %".99"
.98:
  br label %".99"
.99:
  ; SCOPE::if END
  ; OP::cast START
  store [25 x i8] c"pushed data: %i, %i, %i\0a\00", [25 x i8]* %".114"
  %".116" = bitcast [25 x i8]* %".114" to i8*
  ; OP::cast END
  ; OP::call START
  ; OP::index START
  %".120" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"vec", i32 0
  ; OP::index END
  %".122" = call i32 @"Vector_struct_tmp_MMAANNGGLLEE_i32_memberfunction_get"(%"Vector_struct_tmp_MMAANNGGLLEE_i32"* %".120", i32 0)
  ; OP::call end
  ; OP::call START
  ; OP::index START
  %".126" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"vec", i32 0
  ; OP::index END
  %".128" = call i32 @"Vector_struct_tmp_MMAANNGGLLEE_i32_memberfunction_get"(%"Vector_struct_tmp_MMAANNGGLLEE_i32"* %".126", i32 1)
  ; OP::call end
  ; OP::call START
  ; OP::index START
  %".132" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"vec", i32 0
  ; OP::index END
  %".134" = call i32 @"Vector_struct_tmp_MMAANNGGLLEE_i32_memberfunction_get"(%"Vector_struct_tmp_MMAANNGGLLEE_i32"* %".132", i32 2)
  ; OP::call end
  ; OP::call START
  %".137" = call i32 (i8*, ...) @"printf"(i8* %".116", i32 %".122", i32 %".128", i32 %".134")
  ; OP::call end
}

define void @"Vector_struct_tmp_MMAANNGGLLEE_i32_memberfunction_init"(%"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self")
{
entry:
  ; OP::index START
  %".4" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self", i32 0, i32 0
  ; OP::index END
  ; OP::dereference START
  ; OP::dereference END
  ; OP::call START
  %".9" = call i8* @"malloc"(i64 8)
  ; OP::call end
  ; OP::cast START
  %".12" = bitcast i8* %".9" to i32*
  ; OP::cast END
  ; OP::assign START
  store i32* %".12", i32** %".4"
  ; OP::assign END
  ; OP::index START
  %".18" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self", i32 0, i32 1
  ; OP::index END
  ; OP::assign START
  store i32 1, i32* %".18"
  ; OP::assign END
  ; OP::index START
  %".24" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self", i32 0, i32 2
  ; OP::index END
  ; OP::assign START
  store i32 0, i32* %".24"
  ; OP::assign END
  ; OP::return START
  ret void
  ; OP::return END
}

define void @"Vector_struct_tmp_MMAANNGGLLEE_i32_memberfunction_push"(%"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self", i32 %"item")
{
entry:
  ; OP::index START
  %".5" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self", i32 0, i32 0
  ; OP::index END
  ; OP::dereference START
  %".8" = load i32*, i32** %".5"
  ; OP::dereference END
  ; OP::index START
  %".11" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self", i32 0, i32 1
  ; OP::index END
  ; OP::dereference START
  %".14" = load i32, i32* %".11"
  ; OP::dereference END
  ; OP::subtract START
  %".17" = sub i32 %".14", 1
  ; OP::subtract END
  ; OP::index START
  %".20" = getelementptr i32, i32* %".8", i32 %".17"
  ; OP::index END
  ; OP::assign START
  store i32 %"item", i32* %".20"
  ; OP::assign END
  ; OP::index START
  %".26" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self", i32 0, i32 1
  ; OP::index END
  ; OP::index START
  %".29" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self", i32 0, i32 1
  ; OP::index END
  ; OP::dereference START
  %".32" = load i32, i32* %".29"
  ; OP::dereference END
  ; OP::add START
  %".35" = add i32 %".32", 1
  ; OP::add END
  ; OP::assign START
  store i32 %".35", i32* %".26"
  ; OP::assign END
  ; OP::index START
  %".41" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self", i32 0, i32 2
  ; OP::index END
  ; OP::index START
  %".44" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self", i32 0, i32 2
  ; OP::index END
  ; OP::dereference START
  %".47" = load i32, i32* %".44"
  ; OP::dereference END
  ; OP::add START
  %".50" = add i32 %".47", 1
  ; OP::add END
  ; OP::assign START
  store i32 %".50", i32* %".41"
  ; OP::assign END
  ; OP::index START
  %".56" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self", i32 0, i32 0
  ; OP::index END
  ; OP::index START
  %".59" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self", i32 0, i32 0
  ; OP::index END
  ; OP::dereference START
  %".62" = load i32*, i32** %".59"
  ; OP::dereference END
  ; OP::index START
  %".65" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self", i32 0, i32 1
  ; OP::index END
  ; OP::dereference START
  %".68" = load i32, i32* %".65"
  ; OP::dereference END
  ; OP::call START
  %".71" = call i32* @"realloc_tmp_MMAANNGGLLEE_i32"(i32* %".62", i32 %".68")
  ; OP::call end
  ; OP::assign START
  store i32* %".71", i32** %".56"
  ; OP::assign END
  ; OP::return START
  ret void
  ; OP::return END
}

define i32* @"realloc_tmp_MMAANNGGLLEE_i32"(i32* %"ptr", i32 %"new_size")
{
entry:
  ; OP::cast START
  %".5" = bitcast i32* %"ptr" to i8*
  ; OP::cast END
  ; OP::dereference START
  ; OP::dereference END
  ; OP::cast START
  %".10" = sext i32 %"new_size" to i64
  ; OP::cast END
  ; OP::multiply START
  %".13" = mul i64 8, %".10"
  ; OP::multiply END
  ; OP::call START
  %".16" = call i8* @"realloc"(i8* %".5", i64 %".13")
  ; OP::call end
  ; OP::cast START
  %".19" = bitcast i8* %".16" to i32*
  ; OP::cast END
  ; OP::return START
  ret i32* %".19"
  ; OP::return END
}

define i32 @"Vector_struct_tmp_MMAANNGGLLEE_i32_memberfunction_get"(%"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self", i32 %"index")
{
entry:
  ; OP::index START
  %".5" = getelementptr %"Vector_struct_tmp_MMAANNGGLLEE_i32", %"Vector_struct_tmp_MMAANNGGLLEE_i32"* %"self", i32 0, i32 0
  ; OP::index END
  ; OP::dereference START
  %".8" = load i32*, i32** %".5"
  ; OP::dereference END
  ; OP::index START
  %".11" = getelementptr i32, i32* %".8", i32 %"index"
  ; OP::index END
  ; OP::dereference START
  %".14" = load i32, i32* %".11"
  ; OP::dereference END
  ; OP::return START
  ret i32 %".14"
  ; OP::return END
}