create table store
	(store_id		        varchar(15),
	 store_name		    varchar(7),
	 store_address		numeric(4,0),
     store_phone                      ,
     store_time                       ,
	 primary key (store_id)
	);

create table make
	(order_form_id		varchar(15),
	 store_id		varchar(7),
	 primary key (order_form_id),
     foreign key (order_form_id) references order_form (order_form_id),
     foreign key (store_id) references store (store_id)

	);

create table order_form
	(order_form_id		varchar(15),
	 room_number		varchar(7),
	 primary key (building, room_number)
	);

create table order_form_item
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
