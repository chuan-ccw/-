create table store
	(store_id		        varchar(15),
	 store_name		    varchar(7)     ,
	 primary key (store_id)
	);



create table order_form
	(order_form_id		varchar(15),
	 tot_money		varchar(7),
	 

	 primary key (building, room_number)
	 
	);

create table details
	(building		varchar(15),
	 room_number		varchar(7),
	 capacity		numeric(4,0),
	 primary key (building, room_number)
	);

create table item
	(building		varchar(15),
	 room_number		varchar(7),
	 capacity		numeric(4,0),
	 primary key (building, room_number)
	);

create table order
	(building		varchar(15),
	 room_number		varchar(7),
	 capacity		numeric(4,0),
	 primary key (building, room_number)
	);

create table customer
	(building		varchar(15),
	 room_number		varchar(7),
	 capacity		numeric(4,0),
	 primary key (building, room_number)
	);
