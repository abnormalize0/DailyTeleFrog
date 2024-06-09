<template>
    <div class="left-block text-color">
	<div class="avatar-header">
		<img style="width: 45px; height: 45px;" :src="avatarBlock.avatarImgSrc" />
		<div>
			<div class="d-flex justify-start p1">
				{{ avatarBlock.profileName }}
			</div>
			<div class="d-flex justify-start additional-info">
				<div class="p2">{{ avatarBlock.profileTag }}</div>
			</div>
		</div>
		<div class="d-flex icons-container">
			<i class="settings-icon icon"></i>
			<i class="exit-icon icon"></i>
		</div>
	</div>
	<div class="stats-section">
		<div v-if="avatarBlock.rating">
		{{getRating(avatarBlock.rating)}}
		</div>
		<div v-if="avatarBlock.subscribers">
		{{getSubs(avatarBlock.subscribers)}}
		</div>
		<div v-if="avatarBlock.patrons">
		{{getPatrons(avatarBlock.patrons)}}
		</div>
	</div>
    </div>
  </template>
    
  <style scoped>
  .left-block {
    height: 187px;
    width: 235px;
    margin-top: 20px;
  }
  .avatar-header {
    display: flex;
    gap: 15px;
    align-items: center; 
  }
  .stats-section {
    height: 80px;
    gap: 7px;
    margin-top: 30px;
  }
  .icons-container {
    justify-content: right;
    width: 100%;
  }
  </style>
    
  <script>  
  export default {
    name: "AvatarBlockComponent",
    props: {
	avatarBlock: {
		avatarImgSrc: String,
		rating: Number,
		subscribers: Number,
		patrons: Number,
		profileName: String,
		profileTag: String
	}
    },
    data() {
      return {
        
      };
    },
    mounted() {
      
    },
    methods: {
		getRating(amount) {
			return "+" +  amount.toString(10) + " рейтинг";
		},
		getSubs(amount) {
			return amount.toString(10) + " подписчиков";
		},
		getPatrons(amount) {
			return amount.toString(10) + " патронов";
		},
	},
  };
  </script>
    
